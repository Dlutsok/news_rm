import { useState, useEffect } from 'react';
import {
  SaveIcon,
  SettingsIcon,
  ClockIcon,
  NewsIcon,
  GlobalIcon,
  FilterIcon,
  ServerIcon,
  RobotIcon,
  UndoIcon,
  SecurityIcon,
  ChartIcon
} from './ui/icons';
import Card from './ui/Card';
import Button from './ui/Button';
import Input from './ui/Input';
import Toggle from './ui/Toggle';
import Alert from './ui/Alert';
import apiClient from '@utils/api';

const SystemSettings = () => {
  const [settings, setSettings] = useState({});
  const [originalSettings, setOriginalSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    fetchSystemSettings();
  }, []);

  const fetchSystemSettings = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSystemSettings();
      setSettings(data.settings || {});
      setOriginalSettings(data.settings || {});
    } catch (error) {
      console.error('Error fetching system settings:', error);
      setMessage({ type: 'error', text: 'Ошибка загрузки системных настроек' });
    } finally {
      setLoading(false);
    }
  };

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        value: value
      }
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setMessage(null);

      // Подготавливаем данные для отправки
      const settingsToUpdate = {};
      Object.keys(settings).forEach(key => {
        settingsToUpdate[key] = settings[key].value;
      });

      const result = await apiClient.updateSystemSettings(settingsToUpdate);
      setOriginalSettings({ ...settings });
      setMessage({ type: 'success', text: 'Системные настройки успешно обновлены' });
    } catch (error) {
      console.error('Error saving system settings:', error);
      setMessage({ type: 'error', text: error.message || 'Ошибка сохранения настроек' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSettings({ ...originalSettings });
    setMessage(null);
  };

  const hasChanges = () => {
    return JSON.stringify(settings) !== JSON.stringify(originalSettings);
  };

  const renderSettingField = (key, setting) => {
    const { value, type, description } = setting;

    // Скрываем поля с ценами
    if (key.includes('price_per_1k_tokens') || 
        key.includes('dall_e_price') || 
        description.includes('Цена за 1К токенов') ||
        description.includes('Цена за одно изображение') ||
        description.includes('USD')) {
      return null;
    }

    // Специальный селект для выбора модели OpenAI
    if (key === 'openai_generation_model') {
      return (
        <div key={key} className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">{description}</label>
          <select
            value={value}
            onChange={(e) => handleSettingChange(key, e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-corporate-500 focus:ring-corporate-500 sm:text-sm"
          >
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-5-mini">GPT-5-mini</option>
            <option value="gpt-5">GPT-5</option>
          </select>
        </div>
      );
    }

    // Новый селект для модели выжимки
    if (key === 'openai_summary_model') {
      return (
        <div key={key} className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">{description}</label>
          <select
            value={value}
            onChange={(e) => handleSettingChange(key, e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-corporate-500 focus:ring-corporate-500 sm:text-sm"
          >
            <option value="gpt-3.5-turbo-16k">GPT-3.5-turbo-16k</option>
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-5-mini">GPT-5-mini</option>
            <option value="gpt-5">GPT-5</option>
          </select>
        </div>
      );
    }

    if (type === 'bool') {
      return (
        <Toggle
          key={key}
          checked={value === 'true'}
          onChange={(checked) => handleSettingChange(key, checked ? 'true' : 'false')}
          label={description}
        />
      );
    }

    // Особый вид для расходов
    if (key === 'expenses_total_rub') {
      return (
        <div key={key} className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">{description}</label>
          <div className="flex items-center gap-2">
            <input
              type="number"
              value={value}
              min={0}
              onChange={(e) => handleSettingChange(key, String(Math.max(0, parseInt(e.target.value || '0', 10))))}
              className="mt-1 block w-48 rounded-md border-gray-300 shadow-sm focus:border-corporate-500 focus:ring-corporate-500 sm:text-sm"
            />
            <button
              type="button"
              onClick={() => handleSettingChange(key, '0')}
              className="px-3 py-2 text-sm bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Сбросить в 0 ₽
            </button>
            <button
              type="button"
              onClick={() => handleSettingChange(key, String(Number(value || 0) + 25))}
              className="px-3 py-2 text-sm bg-blue-100 text-blue-800 rounded-md hover:bg-blue-200"
              title="Добавить 25 ₽ (стоимость публикации)"
            >
              +25 ₽
            </button>
          </div>
        </div>
      )
    }

    return (
      <Input
        key={key}
        label={description}
        type={type === 'int' ? 'number' : 'text'}
        value={value}
        onChange={(e) => handleSettingChange(key, e.target.value)}
        placeholder={`Введите ${description.toLowerCase()}`}
      />
    );
  };

  const groupSettingsByCategory = () => {
    const groups = {
      system: { title: 'Системные параметры', icon: ServerIcon, settings: {} },
      parsing: { title: 'Парсинг новостей', icon: NewsIcon, settings: {} },
      publishing: { title: 'Публикация', icon: RobotIcon, settings: {} },
      generation: { title: 'Генерация контента', icon: SettingsIcon, settings: {} },
      sources: { title: 'Источники новостей', icon: GlobalIcon, settings: {} },
      filtering: { title: 'Фильтрация контента', icon: FilterIcon, settings: {} },
      monitoring: { title: 'Мониторинг и метрики', icon: ChartIcon, settings: {} },
      integrations: { title: 'Интеграции', icon: GlobalIcon, settings: {} },
      cache: { title: 'Кэширование', icon: ClockIcon, settings: {} },
      security: { title: 'Безопасность', icon: SecurityIcon, settings: {} }
    };

    Object.keys(settings).forEach(key => {
      const setting = settings[key];
      
      // Определяем категорию по ключу настройки (fallback логика)
      let category = 'system'; // По умолчанию
      
      if (key.includes('parsing') || key.includes('news_') || key.includes('article_content') || key.includes('article_min') || key.includes('retries')) {
        category = 'parsing';
      } else if (key.includes('publish') || key.includes('daily_publications')) {
        category = 'publishing';
      } else if (key.includes('article_min_length') || key.includes('article_max_length') || key.includes('summary') || key.includes('seo_') || key.includes('keywords')) {
        category = 'generation';
      } else if (key.includes('_enabled') && (key.includes('medvestnik') || key.includes('ria') || key.includes('remedium') || key.includes('rbc') || key.includes('aig'))) {
        category = 'sources';
      } else if (key.includes('quality') || key.includes('relevance') || key.includes('duplicate')) {
        category = 'filtering';
      } else if (key.includes('metrics') || key.includes('health_check') || key.includes('stats_retention')) {
        category = 'monitoring';
      } else if (key.includes('bitrix_')) {
        category = 'integrations';
      } else if (key.includes('cache')) {
        category = 'cache';
      } else if (key.includes('rate_limit') || key.includes('api_key')) {
        category = 'security';
      }
      
      if (groups[category]) {
        groups[category].settings[key] = setting;
      } else {
        groups.system.settings[key] = setting;
      }
    });

    return groups;
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-corporate-500 border-t-transparent mx-auto mb-4"></div>
        <p className="text-gray-500">Загрузка системных настроек...</p>
      </div>
    );
  }

  const settingGroups = groupSettingsByCategory();

  return (
    <div className="space-y-6">
      {message && (
        <Alert 
          variant={message.type} 
          title={message.type === 'success' ? 'Успешно' : 'Ошибка'}
        >
          {message.text}
        </Alert>
      )}

      {/* Приоритетно выводим выбор модели OpenAI вверху */}
      {settings.openai_generation_model && (
        <Card 
          title={
            <div className="flex items-center">
              <RobotIcon className="mr-2 w-5 h-5 text-corporate-500" />
              Выбор модели OpenAI
            </div>
          }
          padding="lg"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {renderSettingField('openai_generation_model', settings.openai_generation_model)}
            {settings.openai_summary_model && renderSettingField('openai_summary_model', settings.openai_summary_model)}
            {settings.openai_summary_temperature && renderSettingField('openai_summary_temperature', settings.openai_summary_temperature)}
            {settings.openai_summary_max_tokens && renderSettingField('openai_summary_max_tokens', settings.openai_summary_max_tokens)}
          </div>
        </Card>
      )}

      {Object.entries(settingGroups).map(([groupKey, group]) => {
        const Icon = group.icon;
        const hasSettings = Object.keys(group.settings).length > 0;

        if (!hasSettings) return null;

        return (
          <Card 
            key={groupKey}
            title={
              <div className="flex items-center">
                <Icon className="mr-2 w-5 h-5 text-corporate-500" />
                {group.title}
              </div>
            }
            padding="lg"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {Object.entries(group.settings).map(([key, setting]) => 
                renderSettingField(key, setting)
              )}
            </div>
          </Card>
        );
      })}

      {/* Кнопки управления */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200 p-4 flex justify-end space-x-4">
        <Button
          variant="secondary"
          icon={UndoIcon}
          onClick={handleReset}
          disabled={!hasChanges() || saving}
        >
          Сбросить
        </Button>
        <Button
          variant="primary"
          icon={SaveIcon}
          onClick={handleSave}
          loading={saving}
          disabled={!hasChanges()}
        >
          Сохранить настройки
        </Button>
      </div>
    </div>
  );
};

export default SystemSettings;