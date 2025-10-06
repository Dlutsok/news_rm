import React, { useState, useEffect } from 'react';

const DatabaseStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/news/dashboard');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Статистика базы данных</h3>
        <div className="animate-pulse">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
            <div className="h-20 bg-gray-200 rounded-lg"></div>
            <div className="h-20 bg-gray-200 rounded-lg"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Статистика базы данных</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">Ошибка загрузки статистики: {error}</p>
          <button 
            onClick={fetchStats}
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Попробовать снова
          </button>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">📊 Статистика базы данных</h3>
        <p className="text-gray-500">Нет данных</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">📊 Статистика PostgreSQL</h3>
        <button 
          onClick={fetchStats}
          className="text-blue-600 hover:text-blue-800 text-sm"
        >
          🔄 Обновить
        </button>
      </div>

      {/* Общая статистика */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 text-center">
          <div className="text-xl font-bold text-blue-600">{stats.total_articles}</div>
          <div className="text-sm text-blue-800">Всего статей</div>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4 text-center">
          <div className="text-xl font-bold text-green-600">
            {Object.keys(stats.sources).length}
          </div>
          <div className="text-sm text-green-800">Источников</div>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-4 text-center">
          <div className="text-xl font-bold text-purple-600">
            {stats.daily_stats[0]?.count || 0}
          </div>
          <div className="text-sm text-purple-800">Сегодня</div>
        </div>
      </div>

      {/* Статистика по источникам */}
      <div className="mb-6">
        <h4 className="text-md font-medium text-gray-900 mb-3">📰 По источникам:</h4>
        <div className="space-y-2">
          {Object.entries(stats.sources).map(([source, count]) => (
            <div key={source} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <span className="text-sm font-medium text-gray-900 uppercase">{source}</span>
              </div>
              <span className="text-sm font-bold text-blue-600">{count} статей</span>
            </div>
          ))}
        </div>
      </div>

      {/* Статистика за последние дни */}
      <div className="mb-6">
        <h4 className="text-md font-medium text-gray-900 mb-3">📅 За последние дни:</h4>
        <div className="grid grid-cols-7 gap-1">
          {stats.daily_stats.map((day, index) => (
            <div key={day.date} className="text-center">
              <div className="text-xs text-gray-500 mb-1">
                {new Date(day.date).toLocaleDateString('ru-RU', { 
                  day: '2-digit', 
                  month: '2-digit' 
                })}
              </div>
              <div 
                className={`h-8 rounded flex items-center justify-center text-xs font-medium ${
                  day.count > 0 
                    ? 'bg-blue-500 text-white' 
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {day.count}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Последние сессии парсинга */}
      {stats.recent_sessions && stats.recent_sessions.length > 0 && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-3">🔄 Последние сессии:</h4>
          <div className="space-y-2">
            {stats.recent_sessions.slice(0, 3).map((session) => (
              <div key={session.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center space-x-2">
                  <span className={`w-2 h-2 rounded-full ${
                    session.status === 'completed' ? 'bg-green-500' : 
                    session.status === 'failed' ? 'bg-red-500' : 'bg-yellow-500'
                  }`}></span>
                  <span className="text-sm text-gray-700 uppercase">{session.source}</span>
                </div>
                <div className="text-xs text-gray-500">
                  {session.saved} сохранено
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseStats;