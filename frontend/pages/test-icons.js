import React from 'react';
import {
  UsersIcon,
  FilterIcon,
  NewsIcon,
  ViewIcon,
  ViewIconSlash,
  HealthIcon,
  MedicalIcon,
  ImageIcon,
  CommentsIcon,
  RubleIcon,
  ProjectIcon,
  PieChartIcon,
  DownloadIcon,
  ServerIcon,
  DatabaseIcon,
  CheckIcon,
  XIcon,
  RefreshIcon,
  LoadingIcon,
  SettingsIcon,
  GlobalIcon,
  ClockIcon,
  CalendarIcon,
  DocumentIcon,
  EditIcon,
  DeleteIcon,
  SaveIcon,
  ExternalIcon,
  SearchIcon,
  PlusIcon,
  UserIcon,
  KeyIcon,
  SecurityIcon,
  WarningIcon,
  InfoIcon,
  CrownIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ActionIcon,
  AIIcon,
  MenuIcon,
  TrendingIcon,
  FileIcon,
  MicrochipIcon,
  RobotIcon,
  UndoIcon,
  ChartIcon,
  CurrencyIcon,
  OrganizationIcon,
  ResearchIcon,
  HideIcon,
  SignOutIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CloseIcon
} from '../components/ui/icons';

const TestIcons = () => {
  const icons = [
    { name: 'UsersIcon', component: UsersIcon },
    { name: 'FilterIcon', component: FilterIcon },
    { name: 'NewsIcon', component: NewsIcon },
    { name: 'ViewIcon', component: ViewIcon },
    { name: 'ViewIconSlash', component: ViewIconSlash },
    { name: 'HealthIcon', component: HealthIcon },
    { name: 'MedicalIcon', component: MedicalIcon },
    { name: 'ImageIcon', component: ImageIcon },
    { name: 'CommentsIcon', component: CommentsIcon },
    { name: 'RubleIcon', component: RubleIcon },
    { name: 'ProjectIcon', component: ProjectIcon },
    { name: 'PieChartIcon', component: PieChartIcon },
    { name: 'DownloadIcon', component: DownloadIcon },
    { name: 'ServerIcon', component: ServerIcon },
    { name: 'DatabaseIcon', component: DatabaseIcon },
    { name: 'CheckIcon', component: CheckIcon },
    { name: 'XIcon', component: XIcon },
    { name: 'RefreshIcon', component: RefreshIcon },
    { name: 'LoadingIcon', component: LoadingIcon },
    { name: 'SettingsIcon', component: SettingsIcon },
    { name: 'GlobalIcon', component: GlobalIcon },
    { name: 'ClockIcon', component: ClockIcon },
    { name: 'CalendarIcon', component: CalendarIcon },
    { name: 'DocumentIcon', component: DocumentIcon },
    { name: 'EditIcon', component: EditIcon },
    { name: 'DeleteIcon', component: DeleteIcon },
    { name: 'SaveIcon', component: SaveIcon },
    { name: 'ExternalIcon', component: ExternalIcon },
    { name: 'SearchIcon', component: SearchIcon },
    { name: 'PlusIcon', component: PlusIcon },
    { name: 'UserIcon', component: UserIcon },
    { name: 'KeyIcon', component: KeyIcon },
    { name: 'SecurityIcon', component: SecurityIcon },
    { name: 'WarningIcon', component: WarningIcon },
    { name: 'InfoIcon', component: InfoIcon },
    { name: 'CrownIcon', component: CrownIcon },
    { name: 'ChevronDownIcon', component: ChevronDownIcon },
    { name: 'ChevronUpIcon', component: ChevronUpIcon },
    { name: 'ActionIcon', component: ActionIcon },
    { name: 'AIIcon', component: AIIcon },
    { name: 'MenuIcon', component: MenuIcon },
    { name: 'TrendingIcon', component: TrendingIcon },
    { name: 'FileIcon', component: FileIcon },
    { name: 'MicrochipIcon', component: MicrochipIcon },
    { name: 'RobotIcon', component: RobotIcon },
    { name: 'UndoIcon', component: UndoIcon },
    { name: 'ChartIcon', component: ChartIcon },
    { name: 'CurrencyIcon', component: CurrencyIcon },
    { name: 'OrganizationIcon', component: OrganizationIcon },
    { name: 'ResearchIcon', component: ResearchIcon },
    { name: 'HideIcon', component: HideIcon },
    { name: 'SignOutIcon', component: SignOutIcon },
    { name: 'ChevronLeftIcon', component: ChevronLeftIcon },
    { name: 'ChevronRightIcon', component: ChevronRightIcon },
    { name: 'CloseIcon', component: CloseIcon }
  ];

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold mb-8">Тест всех иконок</h1>

      <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-6">
        {icons.map(({ name, component: IconComponent }) => (
          <div key={name} className="flex flex-col items-center p-4 border rounded-lg hover:bg-gray-50">
            <div className="w-8 h-8 mb-2 flex items-center justify-center">
              {IconComponent ? (
                <IconComponent className="w-6 h-6 text-gray-700" />
              ) : (
                <div className="w-6 h-6 bg-red-200 rounded flex items-center justify-center">
                  <span className="text-red-600 text-xs">❌</span>
                </div>
              )}
            </div>
            <span className="text-xs text-center text-gray-600 leading-tight">
              {name}
            </span>
            <span className="text-xs mt-1 px-1 py-0.5 rounded" style={{
              backgroundColor: IconComponent ? '#dcfce7' : '#fecaca',
              color: IconComponent ? '#166534' : '#dc2626'
            }}>
              {IconComponent ? '✓' : '❌'}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-8 p-4 bg-gray-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-4">Статистика</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-gray-600">Всего иконок:</span>
            <span className="ml-2 font-semibold">{icons.length}</span>
          </div>
          <div>
            <span className="text-sm text-gray-600">Работают:</span>
            <span className="ml-2 font-semibold text-green-600">
              {icons.filter(({ component }) => component).length}
            </span>
          </div>
          <div>
            <span className="text-sm text-gray-600">Не работают:</span>
            <span className="ml-2 font-semibold text-red-600">
              {icons.filter(({ component }) => !component).length}
            </span>
          </div>
          <div>
            <span className="text-sm text-gray-600">Успешность:</span>
            <span className="ml-2 font-semibold">
              {Math.round((icons.filter(({ component }) => component).length / icons.length) * 100)}%
            </span>
          </div>
        </div>
      </div>

      <div className="mt-8 p-4 bg-blue-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Отладочная информация</h2>
        <div className="text-sm text-gray-700">
          <p className="mb-1">Проверка импортов из: <code>../components/ui/icons</code></p>
          <p>Если иконка показывается красным крестиком, значит она undefined в импорте.</p>
        </div>
      </div>
    </div>
  );
};

export default TestIcons;