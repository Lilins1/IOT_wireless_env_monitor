// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyBbif7F7nsNcv0X_Cxv4jL0kQb0UL5lNpE",
  authDomain: "front-end-dd305.firebaseapp.com",
  projectId: "front-end-dd305",
  storageBucket: "front-end-dd305.firebasestorage.app",
  messagingSenderId: "856951230276",
  appId: "1:856951230276:web:29423e4af390aaa86c5111",
  measurementId: "G-NRGZ0Z4JRL"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);