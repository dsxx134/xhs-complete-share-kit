package bitbrowser

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

const (
	DefaultAPIPort = 54345
	DefaultAPIHost = "127.0.0.1"
)

// Client 比特浏览器 Local API 客户端
type Client struct {
	host   string
	port   int
	client *http.Client
}

// OpenBrowserRequest 打开浏览器请求
type OpenBrowserRequest struct {
	ID string `json:"id"` // 浏览器窗口 ID
}

// OpenBrowserResponse 打开浏览器响应
type OpenBrowserResponse struct {
	Success bool               `json:"success"`
	Data    *OpenBrowserData   `json:"data,omitempty"`
	Msg     string             `json:"msg,omitempty"`
}

// OpenBrowserData 浏览器数据
type OpenBrowserData struct {
	WS       string `json:"ws"`       // WebSocket 调试地址
	HTTP     string `json:"http"`     // HTTP 调试地址
	Driver   string `json:"driver"`   // Driver 路径
}

// CloseBrowserRequest 关闭浏览器请求
type CloseBrowserRequest struct {
	ID string `json:"id"` // 浏览器窗口 ID
}

// CloseBrowserResponse 关闭浏览器响应
type CloseBrowserResponse struct {
	Success bool   `json:"success"`
	Msg     string `json:"msg,omitempty"`
}

// NewClient 创建比特浏览器客户端
func NewClient(opts ...Option) *Client {
	c := &Client{
		host: DefaultAPIHost,
		port: DefaultAPIPort,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
	for _, opt := range opts {
		opt(c)
	}
	return c
}

// Option 客户端选项
type Option func(*Client)

// WithHost 设置 API 主机地址
func WithHost(host string) Option {
	return func(c *Client) {
		c.host = host
	}
}

// WithPort 设置 API 端口
func WithPort(port int) Option {
	return func(c *Client) {
		c.port = port
	}
}

// baseURL 返回 API 基础 URL
func (c *Client) baseURL() string {
	return fmt.Sprintf("http://%s:%d", c.host, c.port)
}

// OpenBrowser 打开浏览器并获取调试地址
func (c *Client) OpenBrowser(browserID string) (*OpenBrowserData, error) {
	url := c.baseURL() + "/browser/open"
	
	reqBody := OpenBrowserRequest{ID: browserID}
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return nil, fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return nil, fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("read response: %w", err)
	}

	var result OpenBrowserResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("unmarshal response: %w, body: %s", err, string(body))
	}

	if !result.Success {
		return nil, fmt.Errorf("open browser failed: %s", result.Msg)
	}

	if result.Data == nil || result.Data.WS == "" {
		return nil, fmt.Errorf("no websocket address in response")
	}

	return result.Data, nil
}

// CloseBrowser 关闭浏览器
func (c *Client) CloseBrowser(browserID string) error {
	url := c.baseURL() + "/browser/close"
	
	reqBody := CloseBrowserRequest{ID: browserID}
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return fmt.Errorf("marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := c.client.Do(req)
	if err != nil {
		return fmt.Errorf("do request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read response: %w", err)
	}

	var result CloseBrowserResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return fmt.Errorf("unmarshal response: %w, body: %s", err, string(body))
	}

	if !result.Success {
		return fmt.Errorf("close browser failed: %s", result.Msg)
	}

	return nil
}

// GetWebSocketURL 获取浏览器的 WebSocket 调试地址（便捷方法）
func (c *Client) GetWebSocketURL(browserID string) (string, error) {
	data, err := c.OpenBrowser(browserID)
	if err != nil {
		return "", err
	}
	return data.WS, nil
}
