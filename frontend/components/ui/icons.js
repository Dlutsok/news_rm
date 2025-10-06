// Универсальные профессиональные иконки для всего проекта
// Используем Heroicons v2 и Lucide для современного минималистичного дизайна

// Основные иконки из Heroicons v2
export {
  // Навигация и основные действия
  HiOutlineNewspaper as NewsIcon,
  HiOutlineMagnifyingGlass as SearchIcon,
  HiOutlineCog6Tooth as SettingsIcon,
  HiOutlineGlobeAlt as GlobalIcon,
  HiOutlineCurrencyDollar as CurrencyIcon,
  HiOutlineChartBarSquare as ChartIcon,

  // Интерфейс и состояния
  HiOutlineCheckCircle as CheckIcon,
  HiOutlineXCircle as CloseIcon,
  HiOutlineExclamationTriangle as WarningIcon,
  HiOutlineInformationCircle as InfoIcon,
  HiOutlineChevronDown as ChevronDownIcon,
  HiOutlineChevronUp as ChevronUpIcon,
  HiOutlineChevronLeft as ChevronLeftIcon,
  HiOutlineChevronRight as ChevronRightIcon,

  // Контент и медиа
  HiOutlinePhoto as ImageIcon,
  HiOutlineDocument as DocumentIcon,
  HiOutlineCalendar as CalendarIcon,
  HiOutlineClock as ClockIcon,
  HiOutlineEye as ViewIcon,
  HiOutlineEyeSlash as HideIcon,
  HiOutlineEyeSlash as ViewIconSlash,
  HiOutlineChatBubbleLeftRight as CommentsIcon,
  HiOutlineArrowRightOnRectangle as SignOutIcon,

  // Действия пользователя
  HiOutlinePlus as PlusIcon,
  HiOutlineTrash as DeleteIcon,
  HiOutlinePencil as EditIcon,
  HiOutlineArrowDownTray as SaveIcon,
  HiOutlineArrowTopRightOnSquare as ExternalIcon,
  HiOutlineArrowPath as RefreshIcon,
  HiOutlineBolt as ActionIcon,

  // Пользователи и система
  HiOutlineUser as UserIcon,
  HiOutlineUsers as UsersIcon,
  HiOutlineBuildingOffice2 as OrganizationIcon,
  HiOutlineShieldCheck as SecurityIcon,
  HiOutlineKey as KeyIcon,
  HiOutlineTrophy as CrownIcon,
  HiOutlineServerStack as ServerIcon,
  HiOutlineCpuChip as RobotIcon,
  HiOutlineArrowUturnLeft as UndoIcon,
  HiOutlineCpuChip as MicrochipIcon,

  // Медицинские и специализированные
  HiOutlineBeaker as MedicalIcon,
  HiOutlineAcademicCap as ResearchIcon,
  HiOutlineHeart as HealthIcon,
  HiOutlineSparkles as AIIcon,

  // Фильтры и меню
  HiOutlineFunnel as FilterIcon,
  HiOutlineBars3 as MenuIcon,
  HiOutlineXMark as XIcon,

} from 'react-icons/hi2'

// Дополнительные иконки из Lucide
export {
  LuLoader2 as LoadingIcon,
  LuDatabase as DatabaseIcon,
  LuTrendingUp as TrendingIcon,
  LuFileText as FileIcon,
  LuRussianRuble as RubleIcon,
  LuFolderOpen as ProjectIcon,
  LuPieChart as PieChartIcon,
  LuDownload as DownloadIcon,
} from 'react-icons/lu'

// Маппинг старых FontAwesome иконок на новые профессиональные
export const iconMapping = {
  // Основные иконки
  NewsIcon: 'NewsIcon',
  SearchIcon: 'SearchIcon',
  SearchIcon: 'SearchIcon',
  SettingsIcon: 'SettingsIcon',
  GlobalIcon: 'GlobalIcon',
  FaRubleSign: 'RubleIcon',
  FaProjectDiagram: 'ProjectIcon',
  FaChartLine: 'ChartIcon',
  FaChartBar: 'ChartIcon',
  FaChartPie: 'PieChartIcon',
  FaFileDownload: 'DownloadIcon',
  FaRobot: 'RobotIcon',
  FaUndo: 'UndoIcon',
  FaShieldAlt: 'SecurityIcon',
  FaMicrochip: 'MicrochipIcon',
  FaHeart: 'HealthIcon',
  FaRefresh: 'RefreshIcon',

  // Состояния и обратная связь
  CheckIcon: 'CheckIcon',
  CheckIconCircle: 'CheckIcon',
  XIcon: 'CloseIcon',
  FaXmark: 'XIcon',
  FaStop: 'CloseIcon',
  WarningIcon: 'WarningIcon',
  InfoIcon: 'InfoIcon',

  // Навигация
  FaChevronDown: 'ChevronDownIcon',
  FaChevronUp: 'ChevronUpIcon',
  FaChevronLeft: 'ChevronLeftIcon',
  FaChevronRight: 'ChevronRightIcon',

  // Контент
  FaImage: 'ImageIcon',
  FaPhoto: 'ImageIcon',
  CalendarIcon: 'CalendarIcon',
  ClockIcon: 'ClockIcon',
  ViewIcon: 'ViewIcon',
  ViewIconSlash: 'HideIcon',

  // Действия
  PlusIcon: 'PlusIcon',
  DeleteIcon: 'DeleteIcon',
  EditIcon: 'EditIcon',
  EditIcon: 'EditIcon',
  SaveIcon: 'SaveIcon',
  ExternalIcon: 'ExternalIcon',
  RefreshIcon: 'RefreshIcon',
  FaRefresh: 'RefreshIcon',
  ActionIcon: 'ActionIcon',
  ActionIcon: 'ActionIcon',

  // Пользователи
  UserIcon: 'UserIcon',
  UsersIcon: 'UsersIcon',

  // Загрузка
  LoadingIcon: 'LoadingIcon',

  // Медицинские
  FaHospital: 'OrganizationIcon',
  FaPills: 'MedicalIcon',
  FaMicroscope: 'ResearchIcon',
  FaBaby: 'HealthIcon',

  // Система
  DatabaseIcon: 'DatabaseIcon',
  KeyIcon: 'KeyIcon',
  FilterIcon: 'FilterIcon',
}