import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Products } from '@/client/sdk.gen';
import type { ProductCreate, ProductUpdate } from '@/client/types.gen';

export function useProducts(limit?: number) {
  return useQuery({
    queryKey: ['products', { limit }],
    queryFn: async () => {
      try {
        const response = await Products.listProducts({
          query: { limit: limit || 20 }
        });
        return response.data;
      } catch (error) {
        console.warn('API call failed, using mock data:', error);
        // Return mock data if API fails
        return MOCK_PRODUCTS.slice(0, limit || 20);
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1, // Only retry once
  });
}

export function useProduct(productId: string) {
  return useQuery({
    queryKey: ['product', productId],
    queryFn: async () => {
      try {
        const response = await Products.getProduct({
          path: { product_id: productId }
        });
        return response.data;
      } catch (error) {
        console.warn('API call failed for product:', productId, error);
        // Return mock product if API fails
        return MOCK_PRODUCTS.find(p => p.id === productId);
      }
    },
    enabled: !!productId,
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  });
}

export function useFeaturedProducts(limit: number = 8) {
  return useQuery({
    queryKey: ['featured-products', { limit }],
    queryFn: async () => {
      try {
        const response = await Products.listProducts({
          query: { limit }
        });
        return response.data;
      } catch (error) {
        console.warn('API call failed, using mock featured products:', error);
        // Return mock data if API fails
        return MOCK_PRODUCTS.slice(0, limit);
      }
    },
    staleTime: 10 * 60 * 1000, // 10 minutes
    retry: 1,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (productData: ProductCreate) => {
      const response = await Products.createProduct({
        body: productData,
      });
      return response.data;
    },
    onSuccess: () => {
      // Invalidate and refetch products
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ productId, productData }: { productId: string; productData: ProductUpdate }) => {
      const response = await Products.updateProduct({
        path: { product_id: productId },
        body: productData,
      });
      return response.data;
    },
    onSuccess: (_, { productId }) => {
      // Invalidate and refetch specific product and products list
      queryClient.invalidateQueries({ queryKey: ['product', productId] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (productId: string) => {
      await Products.deleteProduct({
        path: { product_id: productId },
      });
      return productId;
    },
    onSuccess: () => {
      // Invalidate and refetch products
      queryClient.invalidateQueries({ queryKey: ['products'] });
    },
  });
}

// Mock data for development when API is not available
const MOCK_PRODUCTS = [
  {
    id: '1',
    name: 'Classic Denim Jacket',
    description: 'Timeless denim jacket perfect for any casual occasion',
    price: '89.99',
    sku: 'DJ001-BL-42'
  },
  {
    id: '2',
    name: 'Premium Cotton T-Shirt',
    description: 'Soft, breathable cotton t-shirt in classic white',
    price: '29.99',
    sku: 'TS002-WH-L'
  },
  {
    id: '3',
    name: 'Slim Fit Chinos',
    description: 'Modern slim fit chinos in versatile khaki',
    price: '59.99',
    sku: 'CH003-KH-32'
  },
  {
    id: '4',
    name: 'Leather Crossbody Bag',
    description: 'Stylish leather crossbody bag with adjustable strap',
    price: '79.99',
    sku: 'LB004-BR-ONE'
  }
]; 