import { useMutation, useQuery } from '@tanstack/react-query';
import { Jobs } from '@/client/sdk.gen';
import type { JobStatus, JobType } from '@/client/types.gen';

export function useIndexingJob() {
  return useMutation({
    mutationFn: async ({ productId, imageFile }: { productId: string; imageFile: File }) => {
      const response = await Jobs.createIndexingJob({
        query: { product_id: productId },
        body: { image_file: imageFile },
        headers: { 'content-length': imageFile.size },
      });
      return response.data;
    },
  });
}

export function useQueryingJob() {
  return useMutation({
    mutationFn: async ({ imageFile }: { imageFile: File }) => {
      const response = await Jobs.createQueryingJob({
        body: { image_file: imageFile },
        headers: { 'content-length': imageFile.size },
      });
      return response.data;
    },
  });
}

export function useJobStatus(jobId: string) {
  return useQuery({
    queryKey: ['job-status', jobId],
    queryFn: async () => {
      const response = await Jobs.getJobStatus({
        path: { job_id: jobId }
      });
      return response.data;
    },
    enabled: !!jobId,
    refetchInterval: 2000, // Poll every 2 seconds
    refetchIntervalInBackground: false,
  });
}

export function useJobsList(status?: JobStatus, jobType?: JobType) {
  return useQuery({
    queryKey: ['jobs', { status, jobType }],
    queryFn: async () => {
      const response = await Jobs.listJobs({
        query: { 
          status, 
          job_type: jobType,
          limit: 50 
        }
      });
      return response.data;
    },
    staleTime: 10 * 1000, // 10 seconds
  });
} 