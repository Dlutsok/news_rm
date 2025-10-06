import React, { useState, useEffect } from 'react';
import {
  SearchIcon,
  FilterIcon,
  RefreshIcon,
  ViewIcon,
  GlobalIcon
} from './ui/icons';
import Card from './ui/Card';
import Button from './ui/Button';
import Input from './ui/Input';
import Badge from './ui/Badge';
import Table from './ui/Table';
import Alert from './ui/Alert';

const NewsMonitoring = ({ selectedPlatform }) => {
  const [sources, setSources] = useState([
    { id: 1, name: 'Medvestnik.ru', status: 'active', lastCheck: '2 мин назад', articlesFound: 12 },
    { id: 2, name: 'RIA Novosti (Медицина)', status: 'active', lastCheck: '5 мин назад', articlesFound: 8 },
    { id: 3, name: 'АИГ (Фармация)', status: 'inactive', lastCheck: '1 час назад', articlesFound: 0 },
    { id: 4, name: 'Remedium.ru', status: 'active', lastCheck: '3 мин назад', articlesFound: 5 },
  ]);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const filteredSources = sources.filter(source =>
    source.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getStatusBadge = (status) => {
    if (status === 'active') {
      return <Badge variant="success">Активен</Badge>;
    }
    return <Badge variant="error">Неактивен</Badge>;
  };

  const startMonitoring = () => {
    setIsMonitoring(true);
    // Имитация работы мониторинга
    setTimeout(() => {
      setIsMonitoring(false);
      setLastUpdate(new Date());
    }, 3000);
  };

  return (
    <div className="space-y-8">
      {/* Заголовок и управление */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Мониторинг новостей
          </h1>
          <p className="text-gray-500 mt-1">
            Отслеживание медицинских новостей из внешних источников
          </p>
        </div>
        <Button
          variant="primary"
          icon={RefreshIcon}
          loading={isMonitoring}
          onClick={startMonitoring}
        >
          {isMonitoring ? 'Сканирование...' : 'Запустить сканирование'}
        </Button>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card padding="md">
          <div className="text-center">
            <p className="text-xl font-bold text-corporate-500">
              {filteredSources.length}
            </p>
            <p className="text-sm text-gray-500 mt-1">Источников</p>
          </div>
        </Card>
        <Card padding="md">
          <div className="text-center">
            <p className="text-xl font-bold text-corporate-500">
              {sources.reduce((sum, s) => sum + s.articlesFound, 0)}
            </p>
            <p className="text-sm text-gray-500 mt-1">Новых статей</p>
          </div>
        </Card>
        <Card padding="md">
          <div className="text-center">
            <p className="text-xl font-bold text-success">
              {sources.filter(s => s.status === 'active').length}
            </p>
            <p className="text-sm text-gray-500 mt-1">Активных</p>
          </div>
        </Card>
        <Card padding="md">
          <div className="text-center">
            <p className="text-sm text-gray-500">Последнее обновление</p>
            <p className="font-medium text-gray-900">
              {lastUpdate.toLocaleTimeString('ru-RU')}
            </p>
          </div>
        </Card>
      </div>

      {/* Фильтры и поиск */}
      <Card title="Источники новостей" padding="lg">
        <div className="mb-6 flex gap-4">
          <Input
            icon={SearchIcon}
            placeholder="Поиск источников..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            containerClassName="flex-1"
          />
          <Button variant="secondary" icon={FilterIcon}>
            Фильтры
          </Button>
        </div>

        {/* Таблица источников */}
        <Table>
          <Table.Header>
            <Table.Row>
              <Table.HeaderCell>Источник</Table.HeaderCell>
              <Table.HeaderCell>Статус</Table.HeaderCell>
              <Table.HeaderCell>Последняя проверка</Table.HeaderCell>
              <Table.HeaderCell>Новых статей</Table.HeaderCell>
              <Table.HeaderCell>Действия</Table.HeaderCell>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {filteredSources.map((source) => (
              <Table.Row key={source.id}>
                <Table.Cell>
                  <div className="flex items-center">
                    <GlobalIcon className="w-4 h-4 text-corporate-500 mr-3" />
                    <span className="font-medium">{source.name}</span>
                  </div>
                </Table.Cell>
                <Table.Cell>
                  {getStatusBadge(source.status)}
                </Table.Cell>
                <Table.Cell className="text-gray-500">
                  {source.lastCheck}
                </Table.Cell>
                <Table.Cell>
                  <span className="font-semibold text-corporate-600">
                    {source.articlesFound}
                  </span>
                </Table.Cell>
                <Table.Cell>
                  <div className="flex gap-2">
                    <Button variant="ghost" size="sm" icon={ViewIcon}>
                      Просмотр
                    </Button>
                    <Button variant="ghost" size="sm" icon={RefreshIcon}>
                      Обновить
                    </Button>
                  </div>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table>
      </Card>

      {/* Развитие функционала */}
      <Alert variant="info" title="В разработке">
        Полнофункциональный мониторинг новостей с настройкой источников, 
        автоматическим парсингом и уведомлениями будет добавлен в следующих версиях.
      </Alert>
    </div>
  );
};

export default NewsMonitoring;