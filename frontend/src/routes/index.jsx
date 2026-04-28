import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom';
import Layout from '../components/Layout';
import ProtectedRoute from '../auth/ProtectedRoute';
import SuperadminRoute from '../auth/SuperadminRoute';
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

import CenterListPage from '../features/system/CenterListPage';
import CenterFormPage from '../features/system/CenterFormPage';
import PlaceholderPage from '../components/PlaceholderPage';

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
      { path: 'teachers/:id/edit', element: <TeacherForm /> },
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
  {
    path: '/system',
    element: <SuperadminRoute><Outlet /></SuperadminRoute>,
    children: [
      { index: true, element: <Navigate to="centers" replace /> },
      { path: 'centers', element: <CenterListPage /> },
      { path: 'centers/new', element: <CenterFormPage /> },
    ]
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);

export default router;
