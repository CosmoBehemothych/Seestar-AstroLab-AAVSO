const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');

// Ограничение: предотвращение запуска нескольких копий приложения
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

let mainWindow = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 920,
    minWidth: 640,
    minHeight: 480,
    backgroundColor: '#040711',
    icon: path.join(__dirname, '..', 'Seestar_AstroLab.ico'),
    frame: true,               // Настоящая нативная рамка ОС с системными кнопками _ □ ✕
    autoHideMenuBar: true,     // Скрыть меню браузера
    title: 'Seestar AstroLab by CosmoBehemothych — AAVSO Extended',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
      webSecurity: true
    }
  });

  // Загружаем локальный интерфейс в собственное изолированное окно
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Запрет открытия внешнего браузера:
  // Если внутри приложения пользователь кликает по ссылке, открываем её во встроенном окне,
  // а НЕ вызываем системный Chrome/Firefox/Edge.
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    return {
      action: 'allow',
      overrideBrowserWindowOptions: {
        width: 1100,
        height: 800,
        icon: path.join(__dirname, '..', 'Seestar_AstroLab.ico'),
        autoHideMenuBar: true,
        title: 'Seestar AstroLab — Встроенный просмотр'
      }
    };
  });

  // Автоматическая передача сконвертированных данных в форму AAVSO WebObs (?preview=true)
  mainWindow.webContents.on('did-create-window', (childWin) => {
    childWin.webContents.on('did-finish-load', () => {
      const currentUrl = childWin.webContents.getURL();
      if (currentUrl.includes('apps.aavso.org/v2/data/submit/photometry') && !currentUrl.includes('preview=true')) {
        childWin.webContents.executeJavaScript(`
          (function() {
            try {
              if (!window.name || !window.name.includes('SEESTAR_AAVSO_AUTO_UPLOAD')) return;
              const payload = JSON.parse(window.name);
              if (!payload || !payload.csvContent) return;
              window.name = '';
              const sel = document.querySelector('select[name="_obscount"]');
              if (sel) { sel.value = '2'; sel.dispatchEvent(new Event('change', { bubbles: true })); }
              setTimeout(() => {
                const fileInput = document.querySelector('input[name="obsfile"]') || document.getElementById('id_obsfile');
                if (fileInput) {
                  const dt = new DataTransfer();
                  const file = new File([payload.csvContent], payload.fileName || 'Seestar_AAVSO.csv', { type: 'text/csv' });
                  dt.items.add(file);
                  fileInput.files = dt.files;
                  fileInput.dispatchEvent(new Event('change', { bubbles: true }));
                  const btnContinue = document.querySelector('input[name="continue"]') || document.getElementById('submit-id-continue');
                  if (btnContinue) btnContinue.click();
                }
              }, 350);
            } catch (e) {}
          })();
        `).catch(() => {});
      }
    });
  });

  // Полное закрытие приложения при закрытии окна (никаких фоновых процессов)
  mainWindow.on('closed', () => {
    mainWindow = null;
    app.quit();
  });
}

app.on('second-instance', () => {
  if (mainWindow) {
    if (mainWindow.isMinimized()) mainWindow.restore();
    mainWindow.focus();
  }
});

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  app.quit();
});
