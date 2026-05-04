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
- [x] **Web Icon (Favicon):** Properly centered and linked.
- [x] **Android PWA Icons:** Required sizes (192x192, 512x512) exist and are registered.
- [x] **Maskable Icons:** Registered to ensure safe cropping on Android.
- [x] **iOS Apple Touch Icon:** Created and explicitly linked.
- [x] **Theme Color:** Status bar color matches the app design.

### 📥 B. Installation Experience
- [x] **Install Prompt Logic:** correctly listens and reacts to installation availability.
- [x] **Android Installation:** Inline button triggers native modal.
- [x] **iOS Installation:** Instructional text guides user to add manually.
- [x] **Desktop Fallback:** Fails gracefully for unsupported browsers or already-installed states.

### 🚀 C. Native App Feel
- [x] **Viewport Lock:** Pinch-to-zoom is disabled on Android.
- [x] **Double-Tap Prevention:** Double-tap-to-zoom is disabled globally.
- [x] **iOS Safari Prevention:** Native pinch-to-zoom gestures are intercepted and disabled.
- [x] **Standalone Mode:** Browser URL bar and navigation buttons are hidden when launched.

### ⚡ D. Service Worker & Offline Capability
- [x] **Service Worker Registration:** Core workers generate correctly on build.
- [x] **Asset Pre-caching:** Fast subsequent load times via cached core assets.
- [x] **Updates:** Background detection of new app versions functions properly.
