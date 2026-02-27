package configs

var (
	useHeadless = true

	binPath = ""

	// BitBrowser 相关配置
	bitBrowserID   = ""
	bitBrowserHost = "127.0.0.1"
	bitBrowserPort = 54345
)

func InitHeadless(h bool) {
	useHeadless = h
}

// IsHeadless 是否无头模式。
func IsHeadless() bool {
	return useHeadless
}

func SetBinPath(b string) {
	binPath = b
}

func GetBinPath() string {
	return binPath
}

// SetBitBrowserID 设置比特浏览器窗口 ID
func SetBitBrowserID(id string) {
	bitBrowserID = id
}

// GetBitBrowserID 获取比特浏览器窗口 ID
func GetBitBrowserID() string {
	return bitBrowserID
}

// IsBitBrowserMode 是否使用比特浏览器模式
func IsBitBrowserMode() bool {
	return bitBrowserID != ""
}

// SetBitBrowserHost 设置比特浏览器 API 主机
func SetBitBrowserHost(host string) {
	bitBrowserHost = host
}

// GetBitBrowserHost 获取比特浏览器 API 主机
func GetBitBrowserHost() string {
	return bitBrowserHost
}

// SetBitBrowserPort 设置比特浏览器 API 端口
func SetBitBrowserPort(port int) {
	bitBrowserPort = port
}

// GetBitBrowserPort 获取比特浏览器 API 端口
func GetBitBrowserPort() int {
	return bitBrowserPort
}
