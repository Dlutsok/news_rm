import React, { useState } from 'react';

const FormattingOptionsModal = ({
  isOpen,
  onClose,
  onApply,
  initialOptions = null
}) => {
  const [options, setOptions] = useState({
    headings_count: initialOptions?.headings_count ?? 3,
    style: initialOptions?.style ?? 'structured',
    paragraph_length: initialOptions?.paragraph_length ?? 'medium',
    sentences_per_paragraph: initialOptions?.sentences_per_paragraph ?? 3,
    target_length: initialOptions?.target_length ?? 3100,
    use_lists: initialOptions?.use_lists ?? false,
    use_quotes: initialOptions?.use_quotes ?? false
  });

  const [activePreset, setActivePreset] = useState('custom');

  // Предустановленные настройки
  const presets = {
    news: {
      name: 'Новостная статья',
      description: 'Краткая, структурированная подача с заголовками',
      options: {
        headings_count: 4,
        style: 'structured',
        paragraph_length: 'short',
        sentences_per_paragraph: 2,
        target_length: 2800,
        use_lists: true,
        use_quotes: true
      }
    },
    scientific: {
      name: 'Научная статья',
      description: 'Подробное изложение с научной строгостью',
      options: {
        headings_count: 6,
        style: 'structured',
        paragraph_length: 'long',
        sentences_per_paragraph: 4,
        target_length: 5000,
        use_lists: true,
        use_quotes: true
      }
    },
    narrative: {
      name: 'Повествовательная',
      description: 'Свободное изложение без четкой структуры',
      options: {
        headings_count: 1,
        style: 'narrative',
        paragraph_length: 'medium',
        sentences_per_paragraph: 3,
        target_length: 3200,
        use_lists: false,
        use_quotes: false
      }
    },
    clinical: {
      name: 'Клиническая статья',
      description: 'Профессиональный медицинский контент',
      options: {
        headings_count: 5,
        style: 'structured',
        paragraph_length: 'medium',
        sentences_per_paragraph: 3,
        target_length: 4000,
        use_lists: true,
        use_quotes: true
      }
    },
    minimal: {
      name: 'Минималистичная',
      description: 'Без заголовков, только абзацы',
      options: {
        headings_count: 0,
        style: 'narrative',
        paragraph_length: 'medium',
        sentences_per_paragraph: 3,
        target_length: 2500,
        use_lists: false,
        use_quotes: false
      }
    }
  };

  if (!isOpen) return null;

  const handlePresetSelect = (presetKey) => {
    setActivePreset(presetKey);
    if (presetKey !== 'custom') {
      setOptions(presets[presetKey].options);
    }
  };

  const handleOptionChange = (field, value) => {
    setOptions(prev => ({ ...prev, [field]: value }));
    setActivePreset('custom');
  };

  const handleApply = () => {
    onApply(options);
    onClose();
  };

  const getPreviewText = () => {
    const { headings_count, style, paragraph_length, target_length, use_lists, use_quotes } = options;

    let preview = `Статья будет создана в ${
      style === 'structured' ? 'структурированном' :
      style === 'narrative' ? 'повествовательном' : 'смешанном'
    } стиле, `;

    if (headings_count === 0) {
      preview += 'без заголовков, ';
    } else {
      preview += `с ${headings_count} заголовк${headings_count === 1 ? 'ом' : headings_count < 5 ? 'ами' : 'ами'}, `;
    }

    preview += `${
      paragraph_length === 'short' ? 'короткими' :
      paragraph_length === 'medium' ? 'средними' : 'длинными'
    } абзацами `;

    preview += `объемом около ${target_length} символов.`;

    if (use_lists) preview += ' Будут использованы списки.';
    if (use_quotes) preview += ' Будут добавлены цитаты экспертов.';

    return preview;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9996]">
      <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              Настройки форматирования статьи
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Presets */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-3">Быстрые настройки</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
              {Object.entries(presets).map(([key, preset]) => (
                <button
                  key={key}
                  onClick={() => handlePresetSelect(key)}
                  className={`p-3 rounded-lg border text-left transition-colors ${
                    activePreset === key
                      ? 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="font-medium">{preset.name}</div>
                  <div className="text-sm text-gray-600 mt-1">{preset.description}</div>
                </button>
              ))}
              <button
                onClick={() => handlePresetSelect('custom')}
                className={`p-3 rounded-lg border text-left transition-colors ${
                  activePreset === 'custom'
                    ? 'border-purple-500 bg-purple-50 text-purple-700'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                }`}
              >
                <div className="font-medium">Пользовательская</div>
                <div className="text-sm text-gray-600 mt-1">Настроить вручную</div>
              </button>
            </div>
          </div>

          {/* Custom Options */}
          <div className="space-y-6">
            {/* Structure */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Количество заголовков
                </label>
                <select
                  value={options.headings_count}
                  onChange={(e) => handleOptionChange('headings_count', parseInt(e.target.value))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value={0}>Без заголовков</option>
                  <option value={1}>1 заголовок</option>
                  <option value={2}>2 заголовка</option>
                  <option value={3}>3 заголовка</option>
                  <option value={4}>4 заголовка</option>
                  <option value={5}>5 заголовков</option>
                  <option value={6}>6 заголовков</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Стиль написания
                </label>
                <select
                  value={options.style}
                  onChange={(e) => handleOptionChange('style', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="structured">Структурированный</option>
                  <option value="narrative">Повествовательный</option>
                  <option value="mixed">Смешанный</option>
                </select>
              </div>
            </div>

            {/* Paragraphs */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Длина абзацев
                </label>
                <select
                  value={options.paragraph_length}
                  onChange={(e) => handleOptionChange('paragraph_length', e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="short">Короткие (1-2 предложения)</option>
                  <option value="medium">Средние (3-4 предложения)</option>
                  <option value="long">Длинные (5+ предложений)</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Предложений в абзаце
                </label>
                <select
                  value={options.sentences_per_paragraph}
                  onChange={(e) => handleOptionChange('sentences_per_paragraph', parseInt(e.target.value))}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value={1}>1 предложение</option>
                  <option value={2}>2 предложения</option>
                  <option value={3}>3 предложения</option>
                  <option value={4}>4 предложения</option>
                  <option value={5}>5 предложений</option>
                </select>
              </div>
            </div>

            {/* Length */}
            {/*
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Целевая длина статьи: {options.target_length} символов
              </label>
              <input
                type="range"
                min="2500"
                max="3500"
                step="100"
                value={options.target_length}
                onChange={(e) => handleOptionChange('target_length', parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #9333ea 0%, #9333ea ${((options.target_length - 2500) / (3500 - 2500)) * 100}%, #e5e7eb ${((options.target_length - 2500) / (3500 - 2500)) * 100}%, #e5e7eb 100%)`
                }}
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>2500</span>
                <span>3000</span>
                <span>3500</span>
              </div>
            </div>
            */}

            {/* Additional Options */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="use_lists"
                  checked={options.use_lists}
                  onChange={(e) => handleOptionChange('use_lists', e.target.checked)}
                  className="w-4 h-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="use_lists" className="ml-2 text-sm text-gray-700">
                  Использовать списки
                </label>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="use_quotes"
                  checked={options.use_quotes}
                  onChange={(e) => handleOptionChange('use_quotes', e.target.checked)}
                  className="w-4 h-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                />
                <label htmlFor="use_quotes" className="ml-2 text-sm text-gray-700">
                  Добавлять цитаты экспертов
                </label>
              </div>
            </div>

            {/* Preview */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">Превью форматирования</h4>
              <p className="text-blue-800 text-sm">{getPreviewText()}</p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-6 mt-6 border-t">
            <button
              onClick={onClose}
              className="px-6 py-3 text-gray-600 hover:text-gray-800 transition-colors"
            >
              Отмена
            </button>

            <button
              onClick={handleApply}
              className="flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Применить настройки
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FormattingOptionsModal;