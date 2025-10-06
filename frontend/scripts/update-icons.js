#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Маппинг старых FontAwesome иконок на новые
const iconMapping = {
  'FaCalendar': 'CalendarIcon',
  'FaClock': 'ClockIcon',
  'FaEye': 'ViewIcon',
  'FaInfoCircle': 'InfoIcon',
  'FaPlus': 'PlusIcon',
  'FaExternalLinkAlt': 'ExternalIcon',
  'FaTrash': 'DeleteIcon',
  'FaFilter': 'FilterIcon',
  'FaSync': 'RefreshIcon',
  'FaUser': 'UserIcon',
  'FaTimes': 'XIcon',
  'FaExclamationTriangle': 'WarningIcon',
  'FaGlobe': 'GlobalIcon',
  'FaCheck': 'CheckIcon',
  'FaSpinner': 'LoadingIcon',
  'FaSave': 'SaveIcon',
  'FaEdit': 'EditIcon',
  'FaPencil': 'EditIcon',
  'FaMagnifyingGlass': 'SearchIcon',
  'FaSearch': 'SearchIcon',
  'FaCog': 'SettingsIcon',
  'FaUsers': 'UsersIcon',
  'FaKey': 'KeyIcon',
  'FaDatabase': 'DatabaseIcon',
  'FaNewspaper': 'NewsIcon',
  'FaBolt': 'ActionIcon',
  'FaMagic': 'ActionIcon'
};

// Размеры иконок для замены
const sizeMapping = {
  'text-xl': 'w-5 h-5',
  'text-lg': 'w-4 h-4',
  'text-2xl': 'w-6 h-6',
  'text-3xl': 'w-8 h-8',
  'text-4xl': 'w-10 h-10',
  'h-4 w-4': 'w-4 h-4',
  'h-5 w-5': 'w-5 h-5',
  'size={16}': 'w-4 h-4',
  'size={20}': 'w-5 h-5',
  'size={24}': 'w-6 h-6'
};

function updateIconsInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8');
  let hasChanges = false;

  // Замена иконок
  Object.entries(iconMapping).forEach(([oldIcon, newIcon]) => {
    const regex = new RegExp(oldIcon, 'g');
    if (content.includes(oldIcon)) {
      content = content.replace(regex, newIcon);
      hasChanges = true;
      console.log(`Заменено ${oldIcon} → ${newIcon} в ${filePath}`);
    }
  });

  // Замена размеров иконок
  Object.entries(sizeMapping).forEach(([oldSize, newSize]) => {
    const regex = new RegExp(oldSize, 'g');
    if (content.includes(oldSize)) {
      content = content.replace(regex, newSize);
      hasChanges = true;
    }
  });

  // Удаляем size={число} атрибуты
  content = content.replace(/size=\{\d+\}/g, '');

  if (hasChanges) {
    fs.writeFileSync(filePath, content);
    console.log(`✅ Обновлен файл: ${filePath}`);
  }

  return hasChanges;
}

function updateIconImports(filePath) {
  let content = fs.readFileSync(filePath, 'utf-8');

  // Проверяем, есть ли импорты react-icons/fa
  if (content.includes("from 'react-icons/fa'")) {
    // Извлекаем импортируемые иконки
    const importMatch = content.match(/import\s*{([^}]+)}\s*from\s*['"]react-icons\/fa['"]/);
    if (importMatch) {
      const importedIcons = importMatch[1]
        .split(',')
        .map(icon => icon.trim())
        .filter(icon => iconMapping[icon]);

      const newIcons = [...new Set(importedIcons.map(icon => iconMapping[icon]))];

      // Заменяем импорт
      const newImport = `import {\n  ${newIcons.join(',\n  ')}\n} from './ui/icons'`;

      content = content.replace(
        /import\s*{[^}]+}\s*from\s*['"]react-icons\/fa['"]/,
        newImport
      );

      fs.writeFileSync(filePath, content);
      console.log(`✅ Обновлены импорты в: ${filePath}`);
      return true;
    }
  }

  return false;
}

// Основная функция
function main() {
  const componentsDir = path.join(__dirname, '../components');
  const pagesDir = path.join(__dirname, '../pages');

  console.log('🔄 Начинаем обновление иконок...\n');

  function processDirectory(dir) {
    const files = fs.readdirSync(dir);

    files.forEach(file => {
      const filePath = path.join(dir, file);
      const stat = fs.statSync(filePath);

      if (stat.isDirectory()) {
        processDirectory(filePath);
      } else if (file.endsWith('.js') || file.endsWith('.jsx')) {
        updateIconImports(filePath);
        updateIconsInFile(filePath);
      }
    });
  }

  processDirectory(componentsDir);
  processDirectory(pagesDir);

  console.log('\n✨ Обновление иконок завершено!');
  console.log('Проверьте файлы и запустите проект для проверки.');
}

if (require.main === module) {
  main();
}

module.exports = { updateIconsInFile, updateIconImports };