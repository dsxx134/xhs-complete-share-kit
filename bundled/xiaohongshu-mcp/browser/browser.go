package browser

import (
	"strings"

	"github.com/go-rod/rod"
	"github.com/go-rod/rod/lib/launcher"
	"github.com/sirupsen/logrus"
	"github.com/xpzouying/headless_browser"
	"github.com/xpzouying/xiaohongshu-mcp/bitbrowser"
	"github.com/xpzouying/xiaohongshu-mcp/configs"
	"github.com/xpzouying/xiaohongshu-mcp/cookies"
)

// BrowserInterface 统一浏览器接口
type BrowserInterface interface {
	NewPage() *rod.Page
	Close()
}

type browserConfig struct {
	binPath string
}

type Option func(*browserConfig)

func WithBinPath(binPath string) Option {
	return func(c *browserConfig) {
		c.binPath = binPath
	}
}

// HeadlessBrowserWrapper headless_browser.Browser 的包装器，实现 BrowserInterface
type HeadlessBrowserWrapper struct {
	browser *headless_browser.Browser
}

// NewPage 创建新页面
func (w *HeadlessBrowserWrapper) NewPage() *rod.Page {
	return w.browser.NewPage()
}

// Close 关闭浏览器
func (w *HeadlessBrowserWrapper) Close() {
	w.browser.Close()
}

// BitBrowserWrapper 比特浏览器包装器，实现 BrowserInterface
type BitBrowserWrapper struct {
	browser   *rod.Browser
	browserID string
	client    *bitbrowser.Client
}

// NewPage 获取已有页面或创建新页面
// BitBrowser 模式优先使用已打开的页面（保留登录状态）
func (b *BitBrowserWrapper) NewPage() *rod.Page {
	// 获取所有已打开的页面
	pages, err := b.browser.Pages()
	if err == nil && len(pages) > 0 {
		// 优先查找小红书页面
		for _, p := range pages {
			info, err := p.Info()
			if err == nil && info != nil && info.URL != "" {
				if strings.Contains(info.URL, "xiaohongshu.com") {
					logrus.Debugf("reusing existing XHS page: %s", info.URL)
					return p
				}
			}
		}
		// 没有小红书页面，使用第一个非空白页面
		for _, p := range pages {
			info, err := p.Info()
			if err == nil && info != nil && info.URL != "" && info.URL != "about:blank" {
				logrus.Debugf("reusing existing page: %s", info.URL)
				return p
			}
		}
	}
	// 没有可用页面，创建新页面
	logrus.Debug("creating new page in BitBrowser")
	return b.browser.MustPage()
}

// Close 关闭浏览器连接（不关闭比特浏览器窗口）
func (b *BitBrowserWrapper) Close() {
	if b.browser != nil {
		b.browser.Close()
	}
	logrus.Debugf("disconnected from BitBrowser: %s", b.browserID)
}

// NewBrowser 创建浏览器实例（原有方法，保持兼容）
func NewBrowser(headless bool, options ...Option) *headless_browser.Browser {
	cfg := &browserConfig{}
	for _, opt := range options {
		opt(cfg)
	}

	opts := []headless_browser.Option{
		headless_browser.WithHeadless(headless),
	}
	if cfg.binPath != "" {
		opts = append(opts, headless_browser.WithChromeBinPath(cfg.binPath))
	}

	// 加载 cookies
	cookiePath := cookies.GetCookiesFilePath()
	cookieLoader := cookies.NewLoadCookie(cookiePath)

	if data, err := cookieLoader.LoadCookies(); err == nil {
		opts = append(opts, headless_browser.WithCookies(string(data)))
		logrus.Debugf("loaded cookies from filesuccessfully")
	} else {
		logrus.Warnf("failed to load cookies: %v", err)
	}

	return headless_browser.New(opts...)
}

// NewBitBrowser 创建比特浏览器连接
func NewBitBrowser() (*BitBrowserWrapper, error) {
	browserID := configs.GetBitBrowserID()
	if browserID == "" {
		return nil, nil
	}

	client := bitbrowser.NewClient(
		bitbrowser.WithHost(configs.GetBitBrowserHost()),
		bitbrowser.WithPort(configs.GetBitBrowserPort()),
	)

	// 获取 WebSocket 地址
	wsURL, err := client.GetWebSocketURL(browserID)
	if err != nil {
		return nil, err
	}

	logrus.Infof("connecting to BitBrowser: %s, ws: %s", browserID, wsURL)

	// 连接到比特浏览器
	controlURL := launcher.MustResolveURL(wsURL)
	browser := rod.New().ControlURL(controlURL).MustConnect()

	return &BitBrowserWrapper{
		browser:   browser,
		browserID: browserID,
		client:    client,
	}, nil
}

// NewBrowserAuto 自动选择浏览器模式（比特浏览器优先）- 返回统一接口
func NewBrowserAuto(headless bool, options ...Option) (BrowserInterface, error) {
	// 如果配置了比特浏览器，优先使用
	if configs.IsBitBrowserMode() {
		bb, err := NewBitBrowser()
		if err != nil {
			logrus.Warnf("failed to connect to BitBrowser, fallback to normal mode: %v", err)
		} else if bb != nil {
			logrus.Info("using BitBrowser mode")
			return bb, nil
		}
	}

	// 回退到普通模式，包装为统一接口
	logrus.Info("using headless browser mode")
	return &HeadlessBrowserWrapper{
		browser: NewBrowser(headless, options...),
	}, nil
}
