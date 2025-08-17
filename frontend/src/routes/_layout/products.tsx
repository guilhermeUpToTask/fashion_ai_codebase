import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FASHION_THEME } from "@/lib/constants";
import { Plus, Upload, Edit, Trash2, Image as ImageIcon } from "lucide-react";
import { useProductsWithImages, useCreateProduct, useDeleteProduct } from "@/hooks/useProducts";
import { useIndexingJob } from "@/hooks/useJobs";
import { toast } from "sonner";

export const Route = createFileRoute("/_layout/products")({
  component: ProductsPage,
});

interface ProductFormData {
  name: string;
  description: string;
  price: string;
  sku: string;
}

interface ProductWithImages {
  id?: string;
  name: string;
  description?: string | null;
  price: string;
  sku?: string | null;
  image_ids: string[];
}

//TODO: use product card to show product list

export function ProductsPage() {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState<ProductFormData>({
    name: "",
    description: "",
    price: "",
    sku: "",
  });
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [indexingProductId, setIndexingProductId] = useState<string | null>(null);

  const { data: products = [], isLoading, refetch } = useProductsWithImages(100);
  const createProductMutation = useCreateProduct();
  const deleteProductMutation = useDeleteProduct();
  const indexingJobMutation = useIndexingJob();

  const handleCreateProduct = async () => {
    if (!formData.name || !formData.price) {
      toast.error("Name and price are required");
      return;
    }

    try {
      await createProductMutation.mutateAsync({
        name: formData.name,
        description: formData.description || null,
        price: parseFloat(formData.price),
        sku: formData.sku || null,
      });
      
      toast.success("Product created successfully!");
      setFormData({ name: "", description: "", price: "", sku: "" });
      setShowCreateForm(false);
      refetch();
    } catch {
      toast.error("Failed to create product");
    }
  };

  const handleDeleteProduct = async (productId: string) => {
    if (confirm("Are you sure you want to delete this product?")) {
      try {
        await deleteProductMutation.mutateAsync(productId);
        toast.success("Product deleted successfully!");
        refetch();
      } catch {
        toast.error("Failed to delete product");
      }
    }
  };

  const handleIndexImage = async (productId: string) => {
    if (!selectedImage) {
      toast.error("Please select an image first");
      return;
    }

    try {
      setIndexingProductId(productId);
      await indexingJobMutation.mutateAsync({
        productId,
        imageFile: selectedImage,
      });
      
      toast.success("Image indexing job started! Check jobs for status.");
      setSelectedImage(null);
      setIndexingProductId(null);
    } catch {
      toast.error("Failed to start indexing job");
      setIndexingProductId(null);
    }
  };

  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedImage(file);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className={FASHION_THEME.spacing.container}>
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-[#0F172A]">Product Management</h1>
            <p className="text-[#6B7280] mt-2">
              Create and manage products, then index images for AI-powered search
            </p>
          </div>
          <Button 
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-[#C99B6A] hover:bg-[#B08A5A]"
          >
            <Plus className="w-5 h-5 mr-2" />
            {showCreateForm ? "Cancel" : "Add Product"}
          </Button>
        </div>

        {/* Create Product Form */}
        {showCreateForm && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Create New Product</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Product Name *
                  </label>
                  <Input
                    placeholder="e.g., Classic Denim Jacket"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SKU
                  </label>
                  <Input
                    placeholder="e.g., DJ001-BL-42"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Price *
                  </label>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="99.99"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <Input
                    placeholder="Product description..."
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </div>
              </div>
              <div className="mt-4">
                <Button 
                  onClick={handleCreateProduct}
                  disabled={createProductMutation.isPending}
                  className="bg-[#C99B6A] hover:bg-[#B08A5A]"
                >
                  {createProductMutation.isPending ? "Creating..." : "Create Product"}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Products List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading ? (
            <div className="col-span-full text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C99B6A] mx-auto"></div>
              <p className="mt-4 text-[#6B7280]">Loading products...</p>
            </div>
          ) : products.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">👕</span>
              </div>
              <h3 className="text-xl font-semibold text-[#0F172A] mb-2">
                No products yet
              </h3>
              <p className="text-[#6B7280]">
                Create your first product to get started with AI image indexing
              </p>
            </div>
          ) : (
            products.map((product: ProductWithImages) => (
              <Card key={product.id} className="overflow-hidden">
                {/* Product Image */}
                <div className="aspect-square bg-gray-100 overflow-hidden">
                  {product.image_ids && product.image_ids.length > 0 ? (
                    <img
                      src={`${import.meta.env.VITE_API_URL}/images/${product.image_ids[0]}/download`}
                      alt={product.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        // Fallback to placeholder if image fails to load
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        target.nextElementSibling?.classList.remove('hidden');
                      }}
                    />
                  ) : null}
                  {/* Fallback placeholder (hidden by default if image exists) */}
                  <div className={`aspect-square bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center ${product.image_ids && product.image_ids.length > 0 ? 'hidden' : ''}`}>
                    <div className="text-center">
                      <div className="w-16 h-16 bg-[#C99B6A] rounded-full flex items-center justify-center mx-auto mb-2">
                        <ImageIcon className="w-8 h-8 text-white" />
                      </div>
                      <p className="text-sm text-gray-500">No Image</p>
                    </div>
                  </div>
                </div>

                <CardHeader className="pb-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-lg">{product.name}</CardTitle>
                      {product.sku && (
                        <p className="text-sm text-[#6B7280] font-mono mt-1">
                          SKU: {product.sku}
                        </p>
                      )}
                    </div>
                    <div className="flex space-x-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="text-[#1F6F8B] hover:text-[#1F6F8B] hover:bg-[#1F6F8B]/10"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDeleteProduct(product.id!)}
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0">
                  {product.description && (
                    <p className="text-[#6B7280] text-sm mb-4 line-clamp-2">
                      {product.description}
                    </p>
                  )}
                  
                  <div className="flex justify-between items-center mb-4">
                    <span className="text-xl font-bold text-[#0F172A]">
                      ${parseFloat(product.price).toFixed(2)}
                    </span>
                  </div>

                  {/* Image Indexing Section */}
                  <div className="border-t pt-4">
                    <h4 className="text-sm font-medium text-[#0F172A] mb-3">
                      Index Images for AI Search
                    </h4>
                    
                    <div className="space-y-3">
                      <div>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageSelect}
                          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-[#C99B6A] file:text-white hover:file:bg-[#B08A5A]"
                        />
                      </div>
                      
                      <Button
                        onClick={() => handleIndexImage(product.id!)}
                        disabled={!selectedImage || indexingProductId === product.id}
                        className="w-full bg-[#1F6F8B] hover:bg-[#1A5A6F] text-white"
                        size="sm"
                      >
                        <Upload className="w-4 h-4 mr-2" />
                        {indexingProductId === product.id ? "Indexing..." : "Index Image"}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default ProductsPage; 