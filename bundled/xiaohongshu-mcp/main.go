package main

import (
	"flag"
	"os"

	"github.com/sirupsen/logrus"
	"github.com/xpzouying/xiaohongshu-mcp/configs"
)

func main() {
	var (
		headless       bool
		binPath        string // 浏览器二进制文件路径
		port           string
		bitBrowserID   string // 比特浏览器窗口 ID
		bitBrowserHost string // 比特浏览器 API 主机
		bitBrowserPort int    // 比特浏览器 API 端口
	)
	flag.BoolVar(&headless, "headless", true, "是否无头模式")
	flag.StringVar(&binPath, "bin", "", "浏览器二进制文件路径")
	flag.StringVar(&port, "port", ":18060", "端口")
	flag.StringVar(&bitBrowserID, "bit-browser-id", "", "比特浏览器窗口 ID（设置后将连接已打开的比特浏览器）")
	flag.StringVar(&bitBrowserHost, "bit-browser-host", "127.0.0.1", "比特浏览器 Local API 主机地址")
	flag.IntVar(&bitBrowserPort, "bit-browser-port", 54345, "比特浏览器 Local API 端口")
	flag.Parse()

	if len(binPath) == 0 {
		binPath = os.Getenv("ROD_BROWSER_BIN")
	}

	// 支持环境变量设置比特浏览器 ID
	if bitBrowserID == "" {
		bitBrowserID = os.Getenv("BIT_BROWSER_ID")
	}

	configs.InitHeadless(headless)
	configs.SetBinPath(binPath)
	
	// 配置比特浏览器
	if bitBrowserID != "" {
		configs.SetBitBrowserID(bitBrowserID)
		configs.SetBitBrowserHost(bitBrowserHost)
		configs.SetBitBrowserPort(bitBrowserPort)
		logrus.Infof("BitBrowser mode enabled, ID: %s", bitBrowserID)
	}

	// 初始化服务
	xiaohongshuService := NewXiaohongshuService()

	// 创建并启动应用服务器
	appServer := NewAppServer(xiaohongshuService)
	if err := appServer.Start(port); err != nil {
		logrus.Fatalf("failed to run server: %v", err)
	}
}
