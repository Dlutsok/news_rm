#!/usr/bin/env node

/**
 * Скрипт для автоматической замены относительных импортов на алиасы в frontend
 * Использование: node scripts/migration/fix_frontend_imports.js [--dry-run]
 */

const fs = require('fs');
const path = require('path');

const FRONTEND_ROOT = path.join(__dirname, '../../frontend');
const DRY_RUN = process.argv.includes('--dry-run');

// Маппинг относительных путей к алиасам
const PATH_MAPPINGS = [
  {
    pattern: /from\s+['"`]\.\.\/utils\//g,
    replacement: "from '@utils/"
  },
  {
    pattern: /from\s+['"`]\.\.\/components\//g,
    replacement: "from '@components/"
  },
  {
    pattern: /from\s+['"`]\.\.\/contexts\//g,
    replacement: "from '@contexts/"
  },
  {
    pattern: /from\s+['"`]\.\.\/styles\//g,
    replacement: "from '@styles/"
  },
  {
    pattern: /from\s+['"`]\.\.\/pages\//g,
    replacement: "from '@pages/"
  },
  {
    pattern: /import\s+['"`]\.\.\/styles\//g,
    replacement: "import '@styles/"
  },
  // Глубокие относительные импорты
  {
    pattern: /from\s+['"`]\.\.\/\.\.\/utils\//g,
    replacement: "from '@utils/"
  },
  {
    pattern: /from\s+['"`]\.\.\/\.\.\/components\//g,
    replacement: "from '@components/"
  },
  {
    pattern: /from\s+['"`]\.\.\/\.\.\/contexts\//g,
    replacement: "from '@contexts/"
  }
];

const JS_EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx'];

function isJavaScriptFile(filePath) {
  return JS_EXTENSIONS.includes(path.extname(filePath));
}

function walkDirectory(dir, callback) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stats = fs.statSync(filePath);

    if (stats.isDirectory() && file !== 'node_modules' && file !== '.next') {
      walkDirectory(filePath, callback);
    } else if (stats.isFile() && isJavaScriptFile(filePath)) {
      callback(filePath);
    }
  });
}

function updateImports(filePath) {
  const content = fs.readFileSync(filePath, 'utf8');
  let updatedContent = content;
  let hasChanges = false;

  PATH_MAPPINGS.forEach(({ pattern, replacement }) => {
    const matches = content.match(pattern);
    if (matches) {
      hasChanges = true;
      updatedContent = updatedContent.replace(pattern, replacement);
      console.log(`  - Updated ${matches.length} import(s) in ${path.relative(FRONTEND_ROOT, filePath)}`);
    }
  });

  if (hasChanges && !DRY_RUN) {
    fs.writeFileSync(filePath, updatedContent, 'utf8');
    return true;
  }

  return hasChanges;
}

function main() {
  console.log('🔄 Fixing frontend import paths...');

  if (DRY_RUN) {
    console.log('📝 DRY RUN MODE - no files will be modified');
  }

  let totalFilesProcessed = 0;
  let totalFilesUpdated = 0;

  walkDirectory(FRONTEND_ROOT, (filePath) => {
    totalFilesProcessed++;
    if (updateImports(filePath)) {
      totalFilesUpdated++;
    }
  });

  console.log('✅ Import fix completed:');
  console.log(`   - Files processed: ${totalFilesProcessed}`);
  console.log(`   - Files updated: ${totalFilesUpdated}`);

  if (DRY_RUN && totalFilesUpdated > 0) {
    console.log('\n💡 To apply changes, run without --dry-run flag');
  }
}

if (require.main === module) {
  main();
}