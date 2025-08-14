import { Link } from '@tanstack/react-router';
import { Facebook, Twitter, Instagram, Mail } from 'lucide-react';
import { FASHION_THEME } from '@/lib/constants';

export function Footer() {
  return (
    <footer className="bg-[#0F172A] text-white">
      <div className={FASHION_THEME.spacing.container}>
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Brand */}
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-[#C99B6A] rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">F</span>
                </div>
                <span className="text-xl font-bold">Fashion</span>
              </div>
              <p className="text-gray-300 max-w-md">
                Discover the latest trends in fashion. From casual wear to elegant evening attire, 
                we bring you quality clothing that makes you look and feel amazing.
              </p>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="font-semibold mb-4 text-[#C99B6A]">Quick Links</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/" className="text-gray-300 hover:text-white transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <button className="text-gray-300 hover:text-white transition-colors text-left">
                    Shop
                  </button>
                </li>
                <li>
                  <button className="text-gray-300 hover:text-white transition-colors text-left">
                    Collections
                  </button>
                </li>
                <li>
                  <button className="text-gray-300 hover:text-white transition-colors text-left">
                    About Us
                  </button>
                </li>
              </ul>
            </div>

            {/* Contact & Social */}
            <div>
              <h3 className="font-semibold mb-4 text-[#C99B6A]">Connect</h3>
              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-gray-300">
                  <Mail className="w-4 h-4" />
                  <span>hello@fashion.com</span>
                </div>
                <div className="flex space-x-4">
                  <button className="text-gray-300 hover:text-[#C99B6A] transition-colors">
                    <Facebook className="w-5 h-5" />
                  </button>
                  <button className="text-gray-300 hover:text-[#C99B6A] transition-colors">
                    <Twitter className="w-5 h-5" />
                  </button>
                  <button className="text-gray-300 hover:text-[#C99B6A] transition-colors">
                    <Instagram className="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-700 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-400 text-sm">
              © 2024 Fashion. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <button className="text-gray-400 hover:text-white text-sm transition-colors">
                Privacy Policy
              </button>
              <button className="text-gray-400 hover:text-white text-sm transition-colors">
                Terms of Service
              </button>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
} 