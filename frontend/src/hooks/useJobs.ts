import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Jobs } from "@/client/sdk.gen";
import type { JobStatus, JobType } from "@/client/types.gen";

//TODO: use the use job status to pool the image later
async function waitForJobCompletion(jobId: string, timeoutMs = 30000) {
    const start = Date.now();
    while (true) {
        if (Date.now() - start > timeoutMs) {
            throw new Error("Job did not complete in time");
        }

        const job = await Jobs.getJobStatus({ path: { job_id: jobId } });

        if (job.data?.is_completed) return job.data;
        if (job.data?.is_failed) throw new Error("Job failed");
        await new Promise((res) => setTimeout(res, 2000)); // wait 2s before polling again
    }
}

export function useIndexingJob() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({
            productId,
            imageFile,
        }: {
            productId: string;
            imageFile: File;
        }) => {
            const { data: job } = await Jobs.createIndexingJob({
                query: { product_id: productId },
                body: { image_file: imageFile },
                headers: { "content-length": imageFile.size },
            });

            if (!job?.job_id) throw new Error("Job creation failed");

            await waitForJobCompletion(job.job_id);

            return job;
        },

        onSuccess: (_, { productId }) => {
            queryClient.invalidateQueries({
                queryKey: ["products-with-images"],
            });
            queryClient.invalidateQueries({ queryKey: ["product", productId] });
        },
    });
}

export function useQueryingJob() {
    return useMutation({
        mutationFn: async ({ imageFile }: { imageFile: File }) => {
            const response = await Jobs.createQueryingJob({
                body: { image_file: imageFile },
                headers: { "content-length": imageFile.size },
            });
            return response.data;
        },
    });
}

export function useJobStatus(jobId: string) {
    return useQuery({
        queryKey: ["job-status", jobId],
        queryFn: async () => {
            const response = await Jobs.getJobStatus({
                path: { job_id: jobId },
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
        queryKey: ["jobs", { status, jobType }],
        queryFn: async () => {
            const response = await Jobs.listJobs({
                query: {
                    status,
                    job_type: jobType,
                    limit: 50,
                },
            });
            return response.data;
        },
        staleTime: 10 * 1000, // 10 seconds
    });
}
