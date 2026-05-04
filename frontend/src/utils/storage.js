export const setPersistentItem = (key, value) => {
  localStorage.setItem(key, value);
  const date = new Date();
  date.setTime(date.getTime() + (90 * 24 * 60 * 60 * 1000));
  document.cookie = `${key}=${encodeURIComponent(value)};expires=${date.toUTCString()};path=/;SameSite=Strict`;
};

export const getPersistentItem = (key) => {
  let value = localStorage.getItem(key);
  if (value) return value;
  
  const nameEQ = key + "=";
  const ca = document.cookie.split(';');
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === ' ') c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) {
      value = decodeURIComponent(c.substring(nameEQ.length, c.length));
      // Re-hydrate localStorage if we found it in cookie
      localStorage.setItem(key, value);
      return value;
    }
  }
  return null;
};

export const removePersistentItem = (key) => {
  localStorage.removeItem(key);
  document.cookie = `${key}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/;SameSite=Strict`;
};

export const setSessionItem = (key, value) => {
  sessionStorage.setItem(key, value);
};

export const getSessionItem = (key) => {
  return sessionStorage.getItem(key);
};

export const removeSessionItem = (key) => {
  sessionStorage.removeItem(key);
};
