# 🔏 Сертификат авторства и защита от плагиата (Anti-Plagiarism & Authorship Proof)

**Продукт:** Seestar AstroLab AAVSO (v1.0.0 — Первая версия)  
**Автор и правообладатель:** **CosmoBehemothych**  
**Официальный GitHub:** [https://github.com/CosmoBehemothych](https://github.com/CosmoBehemothych)  
**Официальная страница поддержки:** [https://boosty.to/cosmobehemothych](https://boosty.to/cosmobehemothych)  
**Уникальный криптографический идентификатор (Author Fingerprint):** `CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601`  
**SHA-256 слепок скрытой цифровой печати:** `b53bea58d23a07b1b2f1f3cb184915ec0bc2894fddf779c3e9582b5a1fb90dcc`

---

## 🛡️ Как устроена встроенная в приложение многоуровневая защита авторства

Даже если злоумышленник скопирует код и попытается через автозамену («Найти и заменить») удалить или переписать имя `CosmoBehemothych` в интерфейсе, в приложении заложены **5 независимых скрытых уровней доказательства вашего авторства**:

### 1. Секретная комбинация клавиш (`Ctrl + Alt + Shift + A`) и секретный код `COSMOPROOF`
В работающем приложении (как в десктопной версии `Seestar AstroLab.exe`, так и в веб-версии `index.html`) встроены три скрытых триггера верификации подлинника:
1. Нажмите на клавиатуре **`Ctrl + Alt + Shift + A`** в любом окне программы.
2. Или введите кодовое слово **`COSMOPROOF`** в поле `OBSCODE:` (после проверки поле автоматически вернёт ваш сохранённый код обсерватории).
3. Или откройте консоль разработчика (`F12`) и выполните команду:
   ```javascript
   window.verifyCosmoBehemothychAuthorship()
   ```
При активации любого из этих триггеров приложение расшифровывает скрытую бинарную печать и выводит на экран **Сертификат подлинности разработки CosmoBehemothych** с вашим `Author Fingerprint` и `SHA-256` подписью.

### 2. Стеганографическая шифрованная печать (`XOR 0x5A + Base64`)
Внутри JS-ядра (`_CBH_ENC_SEAL`) и внутри Python-модулей (`desktop_launcher.py`, `seestar_aavso_desktop_pc.py`) зашита строка сертификата, побайтово зашифрованная операцией `XOR 0x5A` и закодированная в `Base64`:
```text
eorFisSKzorBisKKx4rHisKKwHqK+orKis2K+orKisuKxIr4isCKwnpyFQgTHRMUGxZ6Gw8OEhUICRITCnoKCBUVHHNQisWL2oriiuGK5Irsiu+K54riiu9gegk/PykuOyh6GykuKDUWOzh6GxsMCRV6cixrdGp0anq42s56isWK74vaiuiK6ovVeoroiu+L2ovbiuKL1XNQisqK6IvYiuSL2nqK4nqK5YvaiuqK6IrkiuSK64rhiuqK7orqi9iK74rhi9Zgehk1KTc1GD8yPzc1LjIjOTJQHTMuEi84YHoyLi4qKWB1dT0zLjIvOHQ5NTd1GTUpNzUYPzI/NzUuMiM5MlAYNTUpLiNgejIuLiopYHV1ODU1KS4jdC41dTk1KTc1OD8yPzc1LjIjOTJQivyK4ovei9qK5IroiuSK43qK5IvYiuWK74vdiuqL2IrkiuB6chsvLjI1KHocMzQ9PygqKDM0LnNgehkYEncbCQ4IFRYbGHcbGwwJFXdoamhsd2McYh9uG2hrd20ZaR53GGxqa1CKyovai9+K4ovYiu+K4IvYi9mL2orqYHqKyIrqi9qK4orqiueL2HpsenKK+orqiu6K6ovaeovciu+K4YrviuN6GxsMCRV6cXqK/IrviueL2IvaiuqK4YvWiueK6ovVeoveiuSL2IrkiuaK74vYi9qK4ovdiu+L24rgiuqL1XqK4YrqiuuK5IvaiuqL2Irki9qK4ovVegk/PykuOyh6CWlqdQlpagoIFXUJb2p1CW9qCggVcw==
```
В открытом виде слово `CosmoBehemothych` в этой константе **не содержится**, поэтому обычный поиск по тексту (`Ctrl+F`) её не находит, но при вызове `decodeCosmoBehemothychSeal()` или `verify_cosmobehemothych_authorship()` она расшифровывается в полное удостоверение автора:
>  ПОДЛИННИК РАЗРАБОТКИ (ORIGINAL AUTHORSHIP PROOF) | Приложение: Seestar AstroLab AAVSO (v1.0.0 — Первая версия) | Автор и правообладатель: CosmoBehemothych | GitHub: https://github.com/CosmoBehemothych | Boosty: https://boosty.to/cosmobehemothych | Цифровой отпечаток (Author Fingerprint): CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601 | Архитектура: Вариант 6 (Радар целей AAVSO + Центральная фотометрическая лаборатория Seestar S30/S30PRO/S50/S50PRO)

### 3. Скрытые криптографические метки в CSS и DOM-дереве
В корневом каскаде стилей `:root` и в атрибутах корневого контейнера `#appShell` зашиты контрольные суммы:
* `--cbh-fingerprint: "CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601"`
* `--cbh-sha256-anchor: "b53bea58d23a07b1b2f1f3cb184915ec0bc2894fddf779c3e9582b5a1fb90dcc"`
* `data-cbh-fingerprint="CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601"`

### 4. Цифровая атрибуция в ресурсах Windows PE (`VSVersionInfo`)
В метаданных сборки Windows (`version_info.txt` и `Seestar_AstroLab_Installer.iss`) зафиксированы:
* `CompanyName`: `CosmoBehemothych (https://github.com/CosmoBehemothych)`
* `LegalCopyright`: `Copyright (C) 2026 CosmoBehemothych. Fingerprint: CBH-ASTROLAB-AAVSO-2026-9F8E4A21-7C3D-B601`

### 5. Контрольные суммы SHA-256 эталонного релиза v1.0.0
Любой файл вашей эталонной сборки можно сверить командой `certutil -hashfile <файл> SHA256` (в Windows) или `sha256sum <файл>` (в Linux/macOS):

| Файл релиза | Контрольная сумма SHA-256 |
| :--- | :--- |
| `Seestar_AstroLab_Setup.exe` | `10c47e18bf8bdb68d9a6064028c3c7a3e42684779d94d0123564c589594f743f` |
| `Portable/Seestar_AstroLab_Portable.exe` | `a84529664f863883921298ffaef4384384542a6aaeff53acd0304d1a6547153b` |
| `Source_and_Build/pwa_mobile_and_electron/index.html` | `3ce5dfa89441af849fd4aabd0acfc9ef3be888cf43661416d9aef12bb041d442` |
| `Source_and_Build/desktop_launcher.py` | `7932f70f8a0580b473380bfd212ae84f66ed5183f7f8ceef79e1859c8c1ed416` |
| `Source_and_Build/desktop_pc/seestar_aavso_desktop_pc.py` | `de6422889a417151dc3507ebab4ff906a19b35f89d0e6d55f2e168d6ef050177` |
| `Source_and_Build/version_info.txt` | `9ecb5efd2d40f9e67059798bb2339fea879fd3d47ba6dc09c70d440c85bdf582` |
