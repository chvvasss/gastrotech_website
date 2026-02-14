import { useMutation } from "@tanstack/react-query";
import { mediaApi } from "@/lib/api/media";
import { useToast } from "./use-toast";

export function useMediaUpload() {
    const { toast } = useToast();

    return useMutation({
        mutationFn: mediaApi.upload,
        onError: () => {
            toast({
                title: "Hata",
                description: "Dosya yüklenirken bir sorun oluştu.",
                variant: "destructive",
            });
        },
    });
}
