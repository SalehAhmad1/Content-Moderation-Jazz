export default function Navbar() {
    return (
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="text-xl font-semibold text-gray-900">
                🎬 Video Content Moderation
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="https://github.com/yourusername/video-content-moderation"
                target="_blank"
                rel="noopener noreferrer"
                className="text-gray-500 hover:text-gray-700"
              >
              </a>
            </div>
          </div>
        </div>
      </nav>
    );
  }