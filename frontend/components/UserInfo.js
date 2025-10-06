import { useState } from 'react';
import {
  UserIcon,
  CrownIcon,
  ChevronDownIcon,
  SignOutIcon
} from './ui/icons';
import { useAuth } from '@contexts/AuthContext';

const UserInfo = () => {
  const { user, logout, isAdmin } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  if (!user) return null;

  const handleLogout = () => {
    logout();
    setIsDropdownOpen(false);
  };

  const getRoleText = (role) => {
    switch (role) {
      case 'admin':
        return 'Администратор';
      case 'staff':
        return 'Сотрудник';
      default:
        return role;
    }
  };

  const getRoleColor = (role) => {
    switch (role) {
      case 'admin':
        return 'text-yellow-600 bg-yellow-100';
      case 'staff':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="flex items-center space-x-2 px-3 py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 transition-colors duration-200"
      >
        <div className="flex items-center space-x-2">
          <div className="flex items-center justify-center w-8 h-8 bg-blue-100 rounded-full">
            {isAdmin() ? (
              <CrownIcon className="w-4 h-4 text-yellow-600" />
            ) : (
              <UserIcon className="w-4 h-4 text-blue-600" />
            )}
          </div>
          <div className="text-left">
            <div className="text-sm font-medium text-gray-900">
              {user.username}
            </div>
            <div className={`text-xs px-2 py-0.5 rounded-full ${getRoleColor(user.role)}`}>
              {getRoleText(user.role)}
            </div>
          </div>
        </div>
        <ChevronDownIcon
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
            isDropdownOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isDropdownOpen && (
        <>
          {/* Overlay для закрытия dropdown при клике вне */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsDropdownOpen(false)}
          />
          
          {/* Dropdown menu */}
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-20">
            <div className="px-4 py-2 border-b border-gray-100">
              <div className="text-sm font-medium text-gray-900">
                {user.username}
              </div>
              <div className="text-xs text-gray-500">
                {getRoleText(user.role)}
              </div>
            </div>
            
            <button
              onClick={handleLogout}
              className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center space-x-2"
            >
              <SignOutIcon className="w-4 h-4" />
              <span>Выйти</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default UserInfo;