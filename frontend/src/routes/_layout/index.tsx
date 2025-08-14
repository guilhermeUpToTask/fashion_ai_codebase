import { createFileRoute } from "@tanstack/react-router";
import { Hero } from '@/components/Hero';
import { FASHION_THEME } from '@/lib/constants';
import { Brain, Zap, Database, Upload, Search } from 'lucide-react';

export const Route = createFileRoute("/_layout/")({
  component: HomePage,
});

export function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Hero section - ALWAYS visible */}
      <Hero />
      
      {/* How It Works Section */}
      <section className="py-16 bg-white">
        <div className={FASHION_THEME.spacing.container}>
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-4">
              How It Works
            </h2>
            <p className="text-lg text-[#6B7280] max-w-3xl mx-auto">
              Our AI-powered system processes fashion images through multiple stages to create 
              a searchable vector database of clothing items.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">1. Upload Image</h3>
              <p className="text-[#6B7280]">
                Upload a product image or any image containing clothing items
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-[#1F6F8B] rounded-full flex items-center justify-center mx-auto mb-4">
                <Brain className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">2. AI Processing</h3>
              <p className="text-[#6B7280]">
                YOLOv8 detects clothing items, CLIP generates semantic labels
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-4">
                <Database className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">3. Vector Storage</h3>
              <p className="text-[#6B7280]">
                Embeddings and metadata stored in ChromaDB vector database
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-[#1F6F8B] rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="w-8 h-8 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">4. Similarity Search</h3>
              <p className="text-[#6B7280]">
                Find visually similar clothing items using vector similarity
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Technical Features */}
      <section className="py-16 bg-[#F7F7F8]">
        <div className={FASHION_THEME.spacing.container}>
          <div className="text-center mb-12">
            <h2 className="text-3xl lg:text-4xl font-bold text-[#0F172A] mb-6">
              Technical Features
            </h2>
            <p className="text-lg text-[#6B7280] max-w-3xl mx-auto">
              Built with modern AI/ML technologies and scalable infrastructure
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="w-12 h-12 bg-[#C99B6A] rounded-lg flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-3">
                Async Processing
              </h3>
              <p className="text-[#6B7280]">
                Background job processing with Celery and Redis ensures the API remains responsive 
                while handling computationally intensive AI tasks.
              </p>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="w-12 h-12 bg-[#1F6F8B] rounded-lg flex items-center justify-center mb-4">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-3">
                Advanced AI Models
              </h3>
              <p className="text-[#6B7280]">
                YOLOv8 for precise clothing detection and CLIP for semantic understanding, 
                creating rich, searchable representations of fashion items.
              </p>
            </div>
            
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-200">
              <div className="w-12 h-12 bg-[#C99B6A] rounded-lg flex items-center justify-center mb-4">
                <Database className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-3">
                Vector Database
              </h3>
              <p className="text-[#6B7280]">
                ChromaDB stores high-dimensional embeddings enabling fast and accurate 
                similarity search across thousands of fashion items.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}

export default HomePage;
