import React, { useEffect, useMemo, useState } from 'react';
import { FaRedo } from 'react-icons/fa';
import {
  CheckIcon,
  EditIcon,
  XIcon,
  SettingsIcon
} from './ui/icons';
import FormattingOptionsModal from './FormattingOptionsModal';

const SummaryConfirmation = ({ 
  isOpen, 
  onClose, 
  summary, 
  facts, 
  onConfirm, 
  onRegenerate,
  isLoading = false,
}) => {
  const [editedSummary, setEditedSummary] = useState(summary || '');
  const [editedFacts, setEditedFacts] = useState(facts || []);
  const [isEditing, setIsEditing] = useState(false);
  const [isFormattingModalOpen, setIsFormattingModalOpen] = useState(false);
  const [formattingOptions, setFormattingOptions] = useState(null);

  if (!isOpen) return null;

  const handleConfirm = () => {
    onConfirm({
      summary: editedSummary,
      facts: editedFacts,
      formatting_options: formattingOptions
    });
  };

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    setIsEditing(false);
  };

  const handleAddFact = () => {
    setEditedFacts([...(editedFacts || []), '']);
  };

  const handleFactChange = (index, value) => {
    const newFacts = [...(editedFacts || [])];
    newFacts[index] = value;
    setEditedFacts(newFacts);
  };

  const handleRemoveFact = (index) => {
    const newFacts = (editedFacts || []).filter((_, i) => i !== index);
    setEditedFacts(newFacts);
  };


  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9995]">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-800">
              Подтверждение выжимки
            </h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 transition-colors"
              disabled={isLoading}
            >
              <XIcon  />
            </button>
          </div>

          {/* Summary Section */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold text-gray-700">Выжимка статьи</h3>
              {!isEditing && (
                <button
                  onClick={handleEdit}
                  className="flex items-center gap-2 px-3 py-1 text-blue-600 hover:text-blue-800 transition-colors"
                  disabled={isLoading}
                >
                  <EditIcon  />
                  Редактировать
                </button>
              )}
            </div>
            
            {isEditing ? (
              <div>
                <textarea
                  value={editedSummary}
                  onChange={(e) => setEditedSummary(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  rows={6}
                  placeholder="Введите выжимку статьи..."
                />
                <button
                  onClick={handleSaveEdit}
                  className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Сохранить изменения
                </button>
              </div>
            ) : (
              <div className="p-4 bg-gray-50 rounded-lg border">
                <p className="text-gray-800 leading-relaxed">{editedSummary}</p>
              </div>
            )}
          </div>

          {/* Facts Section */}
          <div className="mb-6">
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-lg font-semibold text-gray-700">Ключевые факты</h3>
              {isEditing && (
                <button
                  onClick={handleAddFact}
                  className="px-3 py-1 text-green-600 hover:text-green-800 transition-colors"
                >
                  + Добавить факт
                </button>
              )}
            </div>
            
            <div className="space-y-2">
              {(editedFacts || []).map((fact, index) => (
                <div key={index} className="flex items-center gap-2">
                  {isEditing ? (
                    <>
                      <input
                        type="text"
                        value={fact}
                        onChange={(e) => handleFactChange(index, e.target.value)}
                        className="flex-1 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder={`Факт ${index + 1}`}
                      />
                      <button
                        onClick={() => handleRemoveFact(index)}
                        className="text-red-600 hover:text-red-800 transition-colors"
                      >
                        <XIcon  />
                      </button>
                    </>
                  ) : (
                    <div className="flex items-start gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200 w-full">
                      <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-gray-800">{fact}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>


          {/* Action Buttons */}
          <div className="flex justify-between items-center pt-4 border-t">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsFormattingModalOpen(true)}
                disabled={isLoading}
                className="flex items-center gap-2 px-4 py-2 text-purple-600 border border-purple-200 rounded-lg hover:bg-purple-50 hover:border-purple-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <SettingsIcon  />
                Настроить форматирование
              </button>
              {formattingOptions && (
                <span className="text-sm text-green-600 font-medium">
                  ✓ Настройки применены
                </span>
              )}
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={onRegenerate}
                disabled={isLoading}
                className="flex items-center gap-2 px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <FaRedo  />
                {isLoading ? 'Генерация...' : 'Повторить'}
              </button>

              <button
                onClick={handleConfirm}
                disabled={isLoading || !editedSummary.trim()}
                className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <CheckIcon  />
                {isLoading ? 'Обработка...' : 'Подтвердить'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Formatting Options Modal */}
      <FormattingOptionsModal
        isOpen={isFormattingModalOpen}
        onClose={() => setIsFormattingModalOpen(false)}
        onApply={setFormattingOptions}
        initialOptions={formattingOptions}
      />
    </div>
  );
};

export default SummaryConfirmation;