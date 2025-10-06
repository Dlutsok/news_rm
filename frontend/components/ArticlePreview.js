import React from 'react';
import {
  XIcon,
  GlobalIcon,
  CalendarIcon,
  UserIcon,
  ViewIcon
} from './ui/icons';

const ArticlePreview = ({ 
  isOpen, 
  onClose, 
  articleData, 
  project,
  onPublish,
  isPublishing = false 
}) => {
  if (!isOpen || !articleData) return null;

  const getProjectInfo = (projectType) => {
    const projects = {
      GYNECOLOGY: {
        name: 'Gynecology.school',
        domain: 'gynecology.school',
        color: 'pink'
      },
      THERAPY: {
        name: 'Therapy.school',
        domain: 'therapy.school',
        color: 'blue'
      },
      PEDIATRICS: {
        name: 'Pediatrics.school',
        domain: 'pediatrics.school',
        color: 'green'
      },
    };
    return projects[projectType] || projects.THERAPY;
  };

  const projectInfo = getProjectInfo(project);
  const currentDate = new Date().toLocaleDateString('ru-RU', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });

  const handlePublish = () => {
    onPublish(articleData, project);
  };

  const openImageInNewTab = (imageUrl) => {
    if (imageUrl) {
      window.open(imageUrl, '_blank', 'noopener,noreferrer');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[95vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-3">
              <h2 className="text-2xl font-bold text-gray-800">
                Предпросмотр статьи
              </h2>
              <span className={`px-3 py-1 rounded-full text-sm font-medium bg-${projectInfo.color}-100 text-${projectInfo.color}-800`}>
                {projectInfo.name}
              </span>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              disabled={isPublishing}
            >
              <XIcon  />
            </button>
          </div>

          {/* SEO Preview */}
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
            <h3 className="text-sm font-medium text-gray-700 mb-3">SEO Превью</h3>
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-green-600">
                <GlobalIcon  />
                <span>{projectInfo.domain}</span>
              </div>
              <h4 className="w-4 h-4 text-blue-600 hover:underline cursor-pointer">
                {articleData.seo_title}
              </h4>
              <p className="text-sm text-gray-600">
                {articleData.seo_description}
              </p>
              <div className="flex flex-wrap gap-1 mt-2">
                {articleData.seo_keywords?.map((keyword, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Article Preview */}
          <div className="bg-white border rounded-lg overflow-hidden">
            {/* Article Header */}
            <div className="p-6 border-b">
              <div className="flex items-center gap-4 mb-4">
                <div className={`w-12 h-12 bg-${projectInfo.color}-500 rounded-full flex items-center justify-center text-white font-bold`}>
                  {projectInfo.name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">{projectInfo.name}</h3>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                      <CalendarIcon  />
                      <span>{currentDate}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <UserIcon  />
                      <span>Редакция</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <ViewIcon  />
                      <span>0 просмотров</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                {articleData.seo_title}
              </h1>
              
              <p className="w-4 h-4 text-gray-600 leading-relaxed">
                {articleData.seo_description}
              </p>
            </div>

            {/* Article Image */}
            {articleData.image_url && (
              <div className="px-6 py-4">
                <img
                  src={articleData.image_url}
                  alt={articleData.seo_title}
                  className="w-full h-64 object-cover rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                  onClick={() => openImageInNewTab(articleData.image_url)}
                  title="Нажмите, чтобы открыть в новой вкладке"
                />
                {articleData.image_prompt && (
                  <p className="text-sm text-gray-500 mt-2 italic">
                    {articleData.image_prompt}
                  </p>
                )}
              </div>
            )}

            {/* Article Content */}
            <div className="p-6">
              <div
                className="prose prose-lg max-w-none medical-article"
                dangerouslySetInnerHTML={{ __html: articleData.news_text }}
              />
            </div>

            {/* Article Footer */}
            <div className="px-6 py-4 bg-gray-50 border-t">
              <div className="flex items-center justify-between">
                <div className="flex flex-wrap gap-2">
                  {articleData.seo_keywords?.map((keyword, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-gray-200 text-gray-700 rounded text-sm"
                    >
                      #{keyword}
                    </span>
                  ))}
                </div>
                <div className="text-sm text-gray-500">
                  Опубликовано на {projectInfo.name}
                </div>
              </div>
            </div>
          </div>

          {/* Publication Info */}
          {project && (
            <div className="pt-6 mt-6 border-t">
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <p className="text-sm text-blue-800">
                  <strong>Проект для публикации:</strong> {project.name}
                </p>
                <p className="text-xs text-blue-600 mt-1">
'Статья будет опубликована в этом проекте автоматически'
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-6 mt-6 border-t">
            <button
              onClick={onClose}
              disabled={isPublishing}
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Закрыть
            </button>
            
            <button
              onClick={handlePublish}
              disabled={isPublishing}
              className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <GlobalIcon  />
              {isPublishing ? 'Публикация...' : 'Опубликовать'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ArticlePreview;