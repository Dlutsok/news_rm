import React, { useState, useEffect } from 'react';
import {
  ExternalIcon,
  CalendarIcon,
  RefreshIcon,
  DocumentIcon
} from './ui/icons';
import Card from './ui/Card';
import Button from './ui/Button';
import Badge from './ui/Badge';
import Table from './ui/Table';
import Alert from './ui/Alert';
import apiClient from '@utils/api';

const PublicationInterface = ({ selectedPlatform }) => {
  const [publishedArticles, setPublishedArticles] = useState([]);
  const [loading, setLoading] = useState(true);

  // Загрузка опубликованных статей
  const loadPublishedArticles = async () => {
    setLoading(true);
    try {
      const data = await apiClient.request('/api/news/articles-with-publication-status?limit=100&offset=0');
      if (data) {
        // Фильтруем только опубликованные статьи
        const published = data.filter(article => article.is_published);
        setPublishedArticles(published);
        console.log(`Загружено ${published.length} опубликованных статей`);
      } else {
        console.error('Ошибка загрузки статей:', data);
      }
    } catch (error) {
      console.error('Ошибка при загрузке опубликованных статей:', error);
    } finally {
      setLoading(false);
    }
  };

  // Загрузка при первом рендере
  useEffect(() => {
    loadPublishedArticles();
  }, []);

  // Форматирование даты
  const formatDate = (dateString) => {
    if (!dateString) return 'Не указана';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Получение бейджа проекта
  const getProjectBadge = (projectCode, projectName) => {
    if (!projectCode) {
      return <Badge variant="default">Не указан</Badge>;
    }
    return <Badge variant="primary">{projectName || projectCode}</Badge>;
  };

  return (
    <div className="space-y-8">
      {/* Заголовок и управление */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Публикация статей
          </h1>
          <p className="text-gray-500 mt-1">
            Управление публикацией статей в CMS платформ
          </p>
        </div>
        <Button
          variant="primary"
          icon={RefreshIcon}
          loading={loading}
          onClick={loadPublishedArticles}
        >
          Обновить
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card padding="md">
          <div className="text-center">
            <p className="text-xl font-bold text-corporate-500">
              {publishedArticles.length}
            </p>
            <p className="text-sm text-gray-500 mt-1">Опубликовано</p>
          </div>
        </Card>
        <Card padding="md">
          <div className="text-center">
            <p className="text-xl font-bold text-corporate-500">0</p>
            <p className="text-sm text-gray-500 mt-1">В очереди</p>
          </div>
        </Card>
        <Card padding="md">
          <div className="text-center">
            <p className="text-xl font-bold text-corporate-500">0</p>
            <p className="text-sm text-gray-500 mt-1">Черновики</p>
          </div>
        </Card>
      </div>

      {/* Удалено по запросу: блок "Возможности системы публикации" */}

      {/* Опубликованные статьи */}
      <Card 
        title={`Опубликованные статьи (${publishedArticles.length})`}
        subtitle="История публикаций в CMS платформ"
        padding="lg"
      >
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-corporate-500 border-t-transparent mx-auto mb-4"></div>
            <p className="text-gray-500">Загрузка опубликованных статей...</p>
          </div>
        ) : publishedArticles.length > 0 ? (
          <div className="overflow-hidden">
            <Table>
              <Table.Header>
                <Table.Row>
                  <Table.HeaderCell>Статья</Table.HeaderCell>
                  <Table.HeaderCell>Платформа</Table.HeaderCell>
                  <Table.HeaderCell>Дата публикации</Table.HeaderCell>
                  <Table.HeaderCell>Источник</Table.HeaderCell>
                  <Table.HeaderCell>Действия</Table.HeaderCell>
                </Table.Row>
              </Table.Header>
              <Table.Body>
                {publishedArticles.map((article, index) => (
                  <Table.Row key={article.id || index}>
                    <Table.Cell>
                      <div className="max-w-md">
                        <p className="font-medium text-gray-900 truncate">
                          {article.title}
                        </p>
                        {article.bitrix_id && (
                          <p className="text-xs text-gray-500 mt-1">
                            Bitrix ID: {article.bitrix_id}
                          </p>
                        )}
                      </div>
                    </Table.Cell>
                    <Table.Cell>
                      {getProjectBadge(article.published_project_code, article.published_project_name)}
                    </Table.Cell>
                    <Table.Cell className="text-gray-500">
                      <div className="flex items-center">
                        <CalendarIcon className="mr-2 h-3 w-3" />
                        {formatDate(article.draft_published_at)}
                      </div>
                    </Table.Cell>
                    <Table.Cell>
                      <Badge variant="default">
                        {article.source?.toUpperCase() || 'Неизвестно'}
                      </Badge>
                    </Table.Cell>
                    <Table.Cell>
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={ExternalIcon}
                        onClick={() => window.open(article.url, '_blank')}
                      >
                        Источник
                      </Button>
                    </Table.Cell>
                  </Table.Row>
                ))}
              </Table.Body>
            </Table>
          </div>
        ) : (
          <div className="text-center py-12">
            <DocumentIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 font-medium">Опубликованных статей пока нет</p>
            <p className="text-sm text-gray-400 mt-1">
              Статьи появятся здесь после публикации в CMS
            </p>
          </div>
        )}
      </Card>
    </div>
  );
};

export default PublicationInterface;