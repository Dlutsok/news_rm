import React from 'react';
import {
  CheckIcon,
  LoadingIcon,
  XIcon,
  EditIcon,
  ViewIcon,
  RobotIcon,
  ResearchIcon
} from './ui/icons';

const ProgressModal = ({ 
  isOpen, 
  onClose, 
  currentStep, 
  isGenerating,
  selectedProject,
  articleTitle 
}) => {
  if (!isOpen) return null;

  const steps = [
    {
      id: 'project',
      title: 'Выбор проекта',
      icon: ResearchIcon,
      description: 'Выберите целевой проект для публикации'
    },
    {
      id: 'summary',
      title: 'Создание выжимки',
      icon: RobotIcon,
        description: 'GPT-5 создает краткую выжимку статьи'
    },
    {
      id: 'editing',
      title: 'Генерация статьи',
      icon: EditIcon,
        description: 'GPT-5 генерирует полную статью с SEO и изображением'
    },
    {
      id: 'preview',
      title: 'Предпросмотр',
      icon: ViewIcon,
      description: 'Финальный просмотр перед публикацией'
    }
  ];

  const getStepStatus = (stepId) => {
    const currentIndex = steps.findIndex(s => s.id === currentStep);
    const stepIndex = steps.findIndex(s => s.id === stepId);
    
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return isGenerating ? 'processing' : 'current';
    return 'pending';
  };

  const getStepColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-500 text-white';
      case 'processing': return 'bg-blue-500 text-white';
      case 'current': return 'bg-blue-100 text-blue-600 border-2 border-blue-500';
      default: return 'bg-gray-200 text-gray-500';
    }
  };

  const getProjectInfo = (projectType) => {
    const projects = {
      'gynecology.school': { name: 'Gynecology.school', color: 'pink' },
      'therapy.school': { name: 'Therapy.school', color: 'blue' },
      'pediatrics.school': { name: 'Pediatrics.school', color: 'green' },
    };
    return projects[projectType] || projects['therapy.school'];
  };

  const projectInfo = selectedProject ? getProjectInfo(selectedProject.type) : null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 backdrop-blur-sm flex items-center justify-center z-[9990] p-2 sm:p-4">
      <div className="bg-white rounded-xl sm:rounded-2xl border border-gray-300 max-w-2xl w-full max-h-[95vh] sm:max-h-[90vh] overflow-y-auto shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <div className="flex items-center">
            <RobotIcon className="text-purple-600 mr-2 w-4 h-4" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Генерация новости
              </h2>
              {projectInfo && (
                <p className="text-sm text-gray-600 mt-1">
                  Для проекта <span className={`font-medium text-${projectInfo.color}-600`}>
                    {projectInfo.name}
                  </span>
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isGenerating}
          >
            <XIcon  />
          </button>
        </div>
        
        {/* Article info */}
        {articleTitle && (
          <div className="px-4 py-3 bg-gray-50 border-b">
            <h3 className="font-medium text-gray-900 text-sm line-clamp-2">
              {articleTitle}
            </h3>
          </div>
        )}
        
        {/* Progress Steps */}
        <div className="p-4">
          <div className="space-y-3">
            {steps.map((step, index) => {
              const status = getStepStatus(step.id);
              const Icon = step.icon;
              
              return (
                <div key={step.id} className="flex items-center">
                  {/* Step Icon */}
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full ${getStepColor(status)} transition-all duration-300`}>
                    {status === 'completed' ? (
                      <CheckIcon  />
                    ) : status === 'processing' ? (
                      <LoadingIcon className="animate-spin"  />
                    ) : (
                      <Icon  />
                    )}
                  </div>
                  
                  {/* Step Content */}
                  <div className="ml-3 flex-1">
                    <div className="flex items-center justify-between">
                      <h4 className={`font-medium ${
                        status === 'completed' ? 'text-green-700' :
                        status === 'processing' || status === 'current' ? 'text-blue-700' :
                        'text-gray-500'
                      }`}>
                        {step.title}
                      </h4>
                      {status === 'processing' && (
                        <span className="text-sm text-blue-600 font-medium">
                          Обработка...
                        </span>
                      )}
                      {status === 'completed' && (
                        <span className="text-sm text-green-600 font-medium">
                          Завершено
                        </span>
                      )}
                    </div>
                    <p className={`text-sm mt-1 ${
                      status === 'completed' ? 'text-green-600' :
                      status === 'processing' || status === 'current' ? 'text-blue-600' :
                      'text-gray-500'
                    }`}>
                      {step.description}
                    </p>
                  </div>
                  
                  {/* Connector Line */}
                  {index < steps.length - 1 && (
                    <div className="absolute left-8 mt-8 w-0.5 h-6 bg-gray-200"></div>
                  )}
                </div>
              );
            })}
          </div>
          
          {/* Current Action */}
          {isGenerating && (
            <div className="mt-4 p-3 bg-blue-50 rounded border border-blue-200">
              <div className="flex items-center">
                <LoadingIcon className="animate-spin text-blue-600 mr-3" />
                <div>
                  <p className="text-blue-800 font-medium">
                    {currentStep === 'summary' && 'Создаем выжимку с помощью GPT-5...'}
                    {currentStep === 'editing' && 'Генерируем полную статью с GPT-5...'}
                    {currentStep === 'preview' && 'Подготавливаем предпросмотр...'}
                  </p>
                  <p className="text-blue-600 text-sm mt-1">
                    Это может занять несколько секунд
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="px-4 py-3 bg-gray-50 border-t">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              Этап {steps.findIndex(s => s.id === currentStep) + 1} из {steps.length}
            </div>
            {!isGenerating && (
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-800 transition-colors"
              >
                Закрыть
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressModal;