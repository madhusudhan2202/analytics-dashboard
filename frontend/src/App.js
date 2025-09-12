import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, PieChart, Pie, Cell, AreaChart, Area
} from 'recharts';
import { 
  Users, BookOpen, TrendingUp, Award, Clock, Target,
  RefreshCw, ChevronRight, Activity, PieChart as PieChartIcon
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff00', '#ff00ff'];

function App() {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [studentPerformance, setStudentPerformance] = useState([]);
  const [courseAnalytics, setCourseAnalytics] = useState([]);
  const [enrollmentTrends, setEnrollmentTrends] = useState([]);
  const [completionByCategory, setCompletionByCategory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dataInitialized, setDataInitialized] = useState(false);

  const initializeData = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/initialize-data`);
      setDataInitialized(true);
      await fetchAllData();
    } catch (err) {
      setError('Failed to initialize sample data');
      console.error('Error initializing data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllData = async () => {
    try {
      setLoading(true);
      
      const [statsRes, performanceRes, analyticsRes, trendsRes, categoryRes] = await Promise.all([
        axios.get(`${API}/dashboard-stats`),
        axios.get(`${API}/student-performance`),
        axios.get(`${API}/course-analytics`),
        axios.get(`${API}/enrollment-trends`),
        axios.get(`${API}/completion-by-category`)
      ]);

      setDashboardStats(statsRes.data);
      setStudentPerformance(performanceRes.data);
      setCourseAnalytics(analyticsRes.data);
      setEnrollmentTrends(trendsRes.data);
      setCompletionByCategory(categoryRes.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch dashboard data');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  const StatCard = ({ title, value, icon: Icon, trend, color = "blue" }) => (
    <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500 hover:shadow-xl transition-shadow duration-300">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-600 text-sm font-medium uppercase tracking-wide">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
          {trend && (
            <p className="text-green-600 text-sm mt-1 flex items-center">
              <TrendingUp className="w-4 h-4 mr-1" />
              {trend}
            </p>
          )}
        </div>
        <div className={`bg-${color}-100 p-3 rounded-full`}>
          <Icon className={`w-8 h-8 text-${color}-600`} />
        </div>
      </div>
    </div>
  );

  if (loading && !dataInitialized) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Loading Dashboard</h2>
          <p className="text-gray-600">Setting up your LMS analytics...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboardStats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-xl shadow-lg">
          <h2 className="text-2xl font-bold text-red-600 mb-4">Welcome to LMS Analytics</h2>
          <p className="text-gray-600 mb-6">Initialize sample data to get started with the dashboard</p>
          <button
            onClick={initializeData}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center mx-auto"
          >
            <RefreshCw className="w-5 h-5 mr-2" />
            Initialize Sample Data
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">LMS Analytics Dashboard</h1>
              <p className="text-gray-600 mt-1">Comprehensive learning management system analytics</p>
            </div>
            <button
              onClick={fetchAllData}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors duration-200 flex items-center"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh Data
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Overview Stats */}
        {dashboardStats && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <StatCard
              title="Total Students"
              value={dashboardStats.total_students.toLocaleString()}
              icon={Users}
              color="blue"
            />
            <StatCard
              title="Total Courses"
              value={dashboardStats.total_courses.toLocaleString()}
              icon={BookOpen}
              color="green"
            />
            <StatCard
              title="Active Students"
              value={dashboardStats.active_students.toLocaleString()}
              icon={Activity}
              color="purple"
            />
            <StatCard
              title="Completion Rate"
              value={`${dashboardStats.completion_rate}%`}
              icon={Award}
              color="yellow"
            />
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Enrollment Trends */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">Enrollment Trends</h3>
              <TrendingUp className="w-6 h-6 text-blue-600" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={enrollmentTrends}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Area type="monotone" dataKey="enrollments" stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Completion by Category */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-bold text-gray-800">Completion by Category</h3>
              <PieChartIcon className="w-6 h-6 text-blue-600" />
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={completionByCategory}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ category, completion_rate }) => `${category}: ${completion_rate}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="completion_rate"
                >
                  {completionByCategory.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Student Performance */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Top Student Performance</h3>
            <Target className="w-6 h-6 text-blue-600" />
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={studentPerformance.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="student_name" 
                angle={-45}
                textAnchor="end"
                height={100}
                interval={0}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="courses_completed" fill="#8884d8" name="Completed Courses" />
              <Bar dataKey="average_score" fill="#82ca9d" name="Average Score %" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Course Analytics */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-bold text-gray-800">Course Analytics</h3>
            <BookOpen className="w-6 h-6 text-blue-600" />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Course Title</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Enrollments</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Completed</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Completion Rate</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Avg Score</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Avg Duration (hrs)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {courseAnalytics.slice(0, 10).map((course, index) => (
                  <tr key={course.course_id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-sm text-gray-900">{course.course_title}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{course.total_enrollments}</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{course.completed_enrollments}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        course.completion_rate >= 70 ? 'bg-green-100 text-green-800' :
                        course.completion_rate >= 50 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {course.completion_rate}%
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">{course.average_score}%</td>
                    <td className="px-4 py-3 text-sm text-gray-600">{course.average_duration_hours}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;