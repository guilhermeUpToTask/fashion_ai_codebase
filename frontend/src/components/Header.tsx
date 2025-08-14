import { Link } from '@tanstack/react-router';
import { Search, User, Upload, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { FASHION_THEME } from '@/lib/constants';
import { isLoggedIn } from '@/hooks/useAuth';

export function Header() {
  const loggedIn = isLoggedIn();

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className={FASHION_THEME.spacing.container}>
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-[#C99B6A] rounded-lg flex items-center justify-center">
              <Brain className="text-white w-5 h-5" />
            </div>
            <span className="text-xl font-bold text-[#0F172A]">Fashion AI</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link 
              to="/" 
              className="text-[#0F172A] hover:text-[#C99B6A] transition-colors"
            >
              Home
            </Link>
            <Link 
              to="/products" 
              className="text-[#0F172A] hover:text-[#C99B6A] transition-colors flex items-center space-x-1"
            >
              <Upload className="w-4 h-4" />
              <span>Index Images</span>
            </Link>
            <Link 
              to="/query" 
              className="text-[#0F172A] hover:text-[#1F6F8B] transition-colors flex items-center space-x-1"
            >
              <Search className="w-4 h-4" />
              <span>Search Similar</span>
            </Link>
            <button className="text-[#0F172A] hover:text-[#C99B6A] transition-colors">
              About
            </button>
            {loggedIn && (
              <Link 
                to="/dashboard" 
                className="text-[#0F172A] hover:text-[#C99B6A] transition-colors"
              >
                Dashboard
              </Link>
            )}
          </nav>

          {/* Search Bar */}
          <div className="flex-1 max-w-md mx-8 hidden lg:block">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search indexed products..."
                className="pl-10 bg-gray-50 border-gray-200 focus:border-[#C99B6A] focus:ring-[#C99B6A]"
              />
            </div>
          </div>

          {/* Right Actions */}
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="icon" className="text-[#0F172A] hover:text-[#C99B6A]">
              <Search className="w-5 h-5 lg:hidden" />
            </Button>
            {loggedIn ? (
              <Link to="/dashboard">
                <Button variant="ghost" size="icon" className="text-[#0F172A] hover:text-[#C99B6A]">
                  <User className="w-5 h-5" />
                </Button>
              </Link>
            ) : (
              <Link to="/login">
                <Button variant="ghost" size="icon" className="text-[#0F172A] hover:text-[#C99B6A]">
                  <User className="w-5 h-5" />
                </Button>
              </Link>
            )}
            <Link to="/products">
              <Button variant="ghost" size="icon" className="text-[#0F172A] hover:text-[#C99B6A] relative">
                <Upload className="w-5 h-5" />
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
} 