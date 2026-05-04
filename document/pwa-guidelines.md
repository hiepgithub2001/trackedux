# Progressive Web App (PWA) Guidelines

This document outlines the configurations and best practices implemented in TrackEduX to ensure the Progressive Web App feels and behaves like a native mobile application.

## 1. Installation Experience

We implemented a custom installation experience to handle the differences between Android and iOS natively.

- **Android (Chrome/Edge):** The app intercepts the native `beforeinstallprompt` event. When the user visits the login page, an inline "Install TrackEduX" button is shown. Clicking this button triggers a native Android installation modal.
- **iOS (Safari):** Apple does not support the `beforeinstallprompt` event. For iOS users, the same inline prompt appears on the login page, but instead of an install button, it provides explicit instructions to manually tap the "Share" icon and select "Add to Home Screen".

## 2. iOS Icon and Branding Support

iOS Safari ignores the standard PWA `manifest.json` for app icons. To ensure the app icon appears correctly on the iOS home screen:
- We added an explicit `<link rel="apple-touch-icon" href="/apple-touch-icon.png" />` tag to `index.html`.
- A high-resolution 192x192 icon is explicitly placed in the `public/` directory for Apple devices to consume.
- A `<meta name="theme-color" content="#1677ff" />` tag is included to ensure the mobile device's top status bar matches the application's primary brand color.
- The web browser tab uses a cleanly centered SVG emoji (`favicon.svg`) to prevent rendering artifacts on macOS.

## 3. Native App Feel: Disabling Browser Zoom

To prevent the web app from feeling like a standard webpage (which ruins the illusion of a native app when the screen accidentally zooms in), we implemented a three-layer approach to completely disable double-tap and pinch-to-zoom:

1. **Viewport Meta Tag (`index.html`)**
   We enforce a strict `maximum-scale=1.0` and `user-scalable=no` in the viewport. This is respected by Android and older iOS devices to prevent zooming.
   ```html
   <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
   ```

2. **CSS Touch Action (`index.css`)**
   We enforce `touch-action: manipulation;` on the `body`. This disables the native 300ms click delay and prevents the double-tap-to-zoom gesture on all interactive elements across modern browsers.
   ```css
   body {
     touch-action: manipulation;
   }
   ```

3. **Javascript Event Interception (`main.jsx`)**
   Because modern iOS Safari often ignores `user-scalable=no` for accessibility reasons, we added a global event listener to explicitly intercept and prevent the native Apple pinch-to-zoom gesture (`gesturestart`).
   ```javascript
   // Prevent pinch-to-zoom on iOS Safari
   document.addEventListener('gesturestart', function(e) {
     e.preventDefault();
   });
   ```

These optimizations combined ensure that when TrackEduX is launched from the home screen, it feels rigid, responsive, and native to the device.

## 4. Comprehensive PWA Launch Checklist

Use this checklist to ensure all PWA features are functioning perfectly when deploying or updating the app.

### 📱 A. Branding & App Icons
- [x] **Web Icon (Favicon):** `favicon.svg` is present, properly centered to prevent clipping, and linked in `index.html`.
- [x] **Android PWA Icons:** `pwa-192x192.png` and `pwa-512x512.png` exist in the `public/` directory and are registered in `vite.config.js` (`manifest.icons`).
- [x] **Maskable Icons:** `maskable-icon-512x512.png` exists and is registered in the manifest with `purpose: 'maskable'` to ensure Android can safely round or crop the icon without cutting off the logo.
- [x] **iOS Apple Touch Icon:** `apple-touch-icon.png` exists in the `public/` directory and is explicitly linked in `index.html` via `<link rel="apple-touch-icon" ...>`.
- [x] **Theme Color:** `<meta name="theme-color" content="#..."/>` is set in `index.html` and `manifest.theme_color` matches, ensuring the mobile status bar blends with the app design.

### 📥 B. Installation Experience
- [x] **Install Prompt Logic:** The `InstallPrompt` component is correctly listening to the `beforeinstallprompt` event.
- [x] **Android Installation:** The "Install TrackEduX" button appears dynamically on the login page for Android users, and tapping it triggers the native install modal.
- [x] **iOS Manual Install Instructions:** For iOS devices (detected via User-Agent), the "Install TrackEduX" button is replaced with clear instructional text telling users to tap the "Share" icon and select "Add to Home Screen".
- [x] **Desktop Fallback:** Desktop users who already have the app installed, or browsers that don't support PWA installation, smoothly hide the inline prompt without breaking the UI layout.

### 🚀 C. Native App Feel (Zooming & Interactions)
- [x] **Viewport Lock:** `<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />` is set to stop Android zooming.
- [x] **Double-Tap Zoom Prevention:** `touch-action: manipulation;` is applied to the `body` tag in CSS to stop double-tapping from zooming the UI.
- [x] **iOS Pinch-to-Zoom Prevention:** A `gesturestart` event listener is attached to the `document` in `main.jsx` and calls `e.preventDefault()` to stop Safari's native pinch zooming.
- [x] **Standalone Mode:** The app manifest is configured with `"display": "standalone"`, so when launched from the home screen, the browser's URL bar and navigation buttons are hidden.

### ⚡ D. Service Worker & Offline Capability
- [x] **Service Worker Registration:** `vite-plugin-pwa` successfully generates and registers `sw.js` upon building the frontend.
- [x] **Asset Pre-caching:** Core assets (JS, CSS, HTML, and images) are pre-cached by the service worker so the app loads instantly on subsequent visits.
- [x] **Updates:** When a new version of the app is pushed, the service worker detects the update and safely refreshes or prompts the user to load the latest version.
