import { useState, useEffect } from 'react';
import {
  SaveIcon,
  ViewIcon,
  PlusIcon,
  DeleteIcon,
  CheckIcon,
  XIcon,
  SettingsIcon,
  GlobalIcon,
  KeyIcon,
  UsersIcon
} from '../components/ui/icons';
import ProtectedRoute from '@components/ProtectedRoute';
import UserManager from '@components/UserManager';
import SystemSettings from '@components/SystemSettings';
import Card from '@components/ui/Card';
import Button from '@components/ui/Button';
import Input from '@components/ui/Input';
import Badge from '@components/ui/Badge';
import Table from '@components/ui/Table';
import Alert from '@components/ui/Alert';
import { useAuth } from '@contexts/AuthContext';
import apiClient from '@utils/api';

const Settings = () => {
  const { isAdmin } = useAuth();
  const [bitrixProjects, setBitrixProjects] = useState([]);
  const [appSettings, setAppSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [showPasswords, setShowPasswords] = useState({});
  const [editingProject, setEditingProject] = useState(null);
  const [editingSettings, setEditingSettings] = useState({});
  const [activeTab, setActiveTab] = useState('users');
  const [testingConnection, setTestingConnection] = useState({});

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const data = await apiClient.getSettings();
      setBitrixProjects(data.bitrix_projects || []);
      setAppSettings(data.app_settings || []);
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveBitrixProject = async (projectCode, projectData) => {
    try {
      setSaving(true);
      const url = editingProject === 'new' 
        ? '/api/settings/bitrix-projects'
        : `/api/settings/bitrix-projects/${projectCode}`;
      
      const method = editingProject === 'new' ? 'POST' : 'PUT';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(projectData)
      });

      if (response.ok) {
        const savedProject = await response.json();
        
        if (editingProject === 'new') {
          setBitrixProjects([...bitrixProjects, savedProject]);
        } else {
          setBitrixProjects(bitrixProjects.map(p => 
            p.project_code === projectCode ? savedProject : p
          ));
        }
        
        setEditingProject(null);
      } else {
        const error = await response.json();
        throw new Error(error.detail);
      }
    } catch (error) {
      console.error('Error saving project:', error);
      throw error;
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'users', label: 'Пользователи', icon: UsersIcon },
    { id: 'bitrix', label: 'Bitrix проекты', icon: GlobalIcon },
    { id: 'system', label: 'Система', icon: SettingsIcon },
  ];

  const togglePasswordVisibility = (projectCode) => {
    setShowPasswords(prev => ({
      ...prev,
      [projectCode]: !prev[projectCode]
    }));
  };

  const startEditingProject = (project) => {
    setEditingProject(project?.project_code || 'new');
  };

  const renderTabNavigation = () => (
    <div className="border-b border-gray-200 mb-8">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center transition-colors duration-200 ${
                activeTab === tab.id
                  ? 'border-corporate-500 text-corporate-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Icon className="mr-2 w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>
    </div>
  );

  const renderUsersTab = () => (
    <div className="space-y-6">
      <Card 
        title="Управление пользователями"
        subtitle="Создание и редактирование учетных записей пользователей системы"
        padding="lg"
      >
        <UserManager />
      </Card>
    </div>
  );

  const renderBitrixTab = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Bitrix проекты</h2>
          <p className="text-gray-500 mt-1">Настройка интеграции с CMS платформ</p>
        </div>
        <Button
          variant="primary"
          icon={PlusIcon}
          onClick={() => startEditingProject(null)}
        >
          Добавить проект
        </Button>
      </div>

      {bitrixProjects.length > 0 ? (
        <Card padding="lg">
          <Table>
            <Table.Header>
              <Table.Row>
                <Table.HeaderCell>Код проекта</Table.HeaderCell>
                <Table.HeaderCell>Название</Table.HeaderCell>
                <Table.HeaderCell>URL</Table.HeaderCell>
                <Table.HeaderCell>Статус</Table.HeaderCell>
                <Table.HeaderCell>Действия</Table.HeaderCell>
              </Table.Row>
            </Table.Header>
            <Table.Body>
              {bitrixProjects.map((project) => (
                <Table.Row key={project.project_code}>
                  <Table.Cell>
                    <Badge variant="primary">{project.project_code}</Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <div>
                      <p className="font-medium text-gray-900">{project.display_name}</p>
                      <p className="text-sm text-gray-500">{project.project_name}</p>
                    </div>
                  </Table.Cell>
                  <Table.Cell className="text-gray-500">
                    {project.api_url ? (
                      <a 
                        href={project.api_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-corporate-500 hover:text-corporate-700"
                      >
                        {project.api_url}
                      </a>
                    ) : (
                      'Не настроен'
                    )}
                  </Table.Cell>
                  <Table.Cell>
                    <Badge variant={project.is_active ? 'success' : 'error'}>
                      {project.is_active ? 'Активен' : 'Неактивен'}
                    </Badge>
                  </Table.Cell>
                  <Table.Cell>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => startEditingProject(project)}
                      >
                        Редактировать
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-error hover:text-error"
                      >
                        Удалить
                      </Button>
                    </div>
                  </Table.Cell>
                </Table.Row>
              ))}
            </Table.Body>
          </Table>
        </Card>
      ) : (
        <Card padding="lg">
          <div className="text-center py-12">
            <GlobalIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Проекты не настроены</p>
            <p className="text-sm text-gray-400 mt-1">
              Добавьте первый проект для интеграции с Bitrix CMS
            </p>
          </div>
        </Card>
      )}

      {/* Форма редактирования проекта */}
      {editingProject && (
        <Card 
          title={editingProject === 'new' ? 'Новый проект' : 'Редактирование проекта'}
          padding="lg"
        >
          <ProjectEditForm
            project={editingProject === 'new' ? null : bitrixProjects.find(p => p.project_code === editingProject)}
            onSave={saveBitrixProject}
            onCancel={() => setEditingProject(null)}
            saving={saving}
          />
        </Card>
      )}
    </div>
  );

  const renderSystemTab = () => (
    <div className="space-y-6">
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Системные настройки</h2>
        <p className="text-gray-500 mt-1">Общие параметры работы системы</p>
      </div>
      <SystemSettings />
    </div>
  );

  if (!isAdmin()) {
    return (
      <ProtectedRoute>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <Alert variant="error" title="Доступ запрещен">
            У вас нет прав для просмотра настроек системы.
          </Alert>
        </div>
      </ProtectedRoute>
    );
  }

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          {/* Заголовок */}
          <div className="mb-8">
            <h1 className="text-2xl font-semibold text-gray-900">
              Настройки системы
            </h1>
            <p className="text-gray-500 mt-1">
              Управление конфигурацией Rusmedical News AI
            </p>
          </div>

          {/* Навигация по табам */}
          {renderTabNavigation()}

          {/* Контент табов */}
          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-corporate-500 border-t-transparent mx-auto mb-4"></div>
              <p className="text-gray-500">Загрузка настроек...</p>
            </div>
          ) : (
            <>
              {activeTab === 'users' && renderUsersTab()}
              {activeTab === 'bitrix' && renderBitrixTab()}
              {activeTab === 'system' && renderSystemTab()}
            </>
          )}
        </div>
      </div>
    </ProtectedRoute>
  );
};

// Компонент формы редактирования проекта
const ProjectEditForm = ({ project, onSave, onCancel, saving }) => {
  const [formData, setFormData] = useState({
    project_code: project?.project_code || '',
    project_name: project?.project_name || '',
    display_name: project?.display_name || '',
    api_url: project?.api_url || '',
    api_token: project?.api_token || '',
    iblock_id: project?.iblock_id || 38,
    is_active: project?.is_active !== false,
    description: project?.description || ''
  });

  const [showToken, setShowToken] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await onSave(formData.project_code, formData);
      onCancel();
    } catch (error) {
      // Ошибка обработается в родительском компоненте
    }
  };

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Input
          label="Код проекта"
          value={formData.project_code}
          onChange={(e) => handleChange('project_code', e.target.value)}
          placeholder="GS, TS, PS"
          required
          disabled={project} // Не даем менять код существующего проекта
        />
        <Input
          label="Название проекта"
          value={formData.project_name}
          onChange={(e) => handleChange('project_name', e.target.value)}
          placeholder="gynecology.school"
          required
        />
        <Input
          label="Отображаемое название"
          value={formData.display_name}
          onChange={(e) => handleChange('display_name', e.target.value)}
          placeholder="Гинекология и акушерство"
          required
        />
        <Input
          label="ID инфоблока"
          type="number"
          value={formData.iblock_id}
          onChange={(e) => handleChange('iblock_id', parseInt(e.target.value))}
          placeholder="38"
        />
      </div>

      <Input
        label="API URL"
        value={formData.api_url}
        onChange={(e) => handleChange('api_url', e.target.value)}
        placeholder="https://api.example.com"
        icon={GlobalIcon}
      />

      <div className="relative">
        <Input
          label="API Token"
          type={showToken ? 'text' : 'password'}
          value={formData.api_token}
          onChange={(e) => handleChange('api_token', e.target.value)}
          placeholder="Введите API токен"
          icon={KeyIcon}
        />
        <button
          type="button"
          className="absolute right-3 top-9 text-gray-400 hover:text-gray-600"
          onClick={() => setShowToken(!showToken)}
        >
          {showToken ? <ViewIconSlash /> : <ViewIcon />}
        </button>
      </div>

      <div className="space-y-4">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={formData.is_active}
            onChange={(e) => handleChange('is_active', e.target.checked)}
            className="w-4 h-4 text-corporate-600 focus:ring-corporate-500 border-gray-300 rounded"
          />
          <span className="ml-2 text-sm text-gray-700">Активен</span>
        </label>
      </div>

      <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
        <Button variant="secondary" onClick={onCancel} disabled={saving}>
          Отмена
        </Button>
        <Button 
          type="submit" 
          variant="primary" 
          loading={saving}
          icon={SaveIcon}
        >
          Сохранить
        </Button>
      </div>
    </form>
  );
};

export default Settings;