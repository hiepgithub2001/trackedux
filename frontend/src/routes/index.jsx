import { createBrowserRouter, Navigate } from 'react-router-dom';
import Layout from '../components/Layout';
import ProtectedRoute from '../auth/ProtectedRoute';
import LoginPage from '../auth/LoginPage';
import DashboardPage from '../features/dashboard/DashboardPage';
import StudentList from '../features/students/StudentList';
import StudentForm from '../features/students/StudentForm';
import StudentDetail from '../features/students/StudentDetail';
import TeacherList from '../features/teachers/TeacherList';
import TeacherForm from '../features/teachers/TeacherForm';
import TeacherDetail from '../features/teachers/TeacherDetail';
import WeeklyCalendar from '../features/schedule/WeeklyCalendar';
import ClassesPage from '../features/classes/ClassesPage';
import ClassForm from '../features/schedule/ClassForm';
import ClassDetail from '../features/schedule/ClassDetail';
import AttendancePage from '../features/attendance/AttendancePage';
import TuitionPage from '../features/tuition/TuitionPage';

const PlaceholderPage = ({ title }) => (
  <div style={{ padding: 24 }}>
    <h2>{title}</h2>
    <p>Coming soon...</p>
  </div>
);

const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    path: '/',
    element: (
      <ProtectedRoute roles={['admin', 'staff']}>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'students', element: <StudentList /> },
      { path: 'students/new', element: <StudentForm /> },
      { path: 'students/:id', element: <StudentDetail /> },
      { path: 'students/:id/edit', element: <StudentForm /> },
      { path: 'schedule', element: <WeeklyCalendar /> },
      { path: 'classes', element: <ClassesPage /> },
      { path: 'classes/new', element: <ClassForm /> },
      { path: 'classes/:id', element: <ClassDetail /> },
      { path: 'classes/:id/edit', element: <ClassForm /> },
      { path: 'attendance', element: <AttendancePage /> },
      { path: 'teachers', element: <TeacherList /> },
      { path: 'teachers/new', element: <TeacherForm /> },
      { path: 'teachers/:id', element: <TeacherDetail /> },
      { path: 'tuition', element: <TuitionPage /> },
      { path: 'reports', element: <PlaceholderPage title="Reports" /> },
      { path: 'notifications', element: <PlaceholderPage title="Notifications" /> },
    ],
  },
  {
    path: '/portal',
    element: <ProtectedRoute roles={['parent']}><PlaceholderPage title="Parent Portal" /></ProtectedRoute>,
  },
  {
    path: '/portal/child/:id',
    element: <ProtectedRoute roles={['parent']}><PlaceholderPage title="Child Detail" /></ProtectedRoute>,
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);

export default router;
