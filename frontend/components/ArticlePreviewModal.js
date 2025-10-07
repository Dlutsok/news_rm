import { HiOutlineGlobeAlt, HiOutlineNewspaper, HiXMark } from 'react-icons/hi2'

const ArticlePreviewModal = ({ isOpen, onClose, article }) => {
  if (!isOpen || !article) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl border border-gray-300 p-6 max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-start mb-6 border-b border-gray-200 pb-4">
          <div className="flex-1 pr-4">
            <div className="flex items-center space-x-2 mb-2">
              <HiOutlineNewspaper className="w-6 h-6 text-purple-600" />
              <h2 className="text-2xl font-bold text-gray-900">
                Предварительный просмотр
              </h2>
            </div>
            <div className="flex items-center text-sm text-gray-500 mt-2">
              <HiOutlineGlobeAlt className="w-4 h-4 mr-1" />
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-purple-600 hover:text-purple-700 underline break-all"
              >
                {article.domain}
              </a>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors p-2 hover:bg-gray-100 rounded-lg"
          >
            <HiXMark className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="prose prose-sm max-w-none">
            <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 leading-relaxed">
              {article.text}
            </pre>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm text-gray-600">
            <span className="font-semibold">Символов:</span> {article.text.length}
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium transition-colors"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  )
}

export default ArticlePreviewModal
