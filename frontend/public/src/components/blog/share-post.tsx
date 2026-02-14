"use client";

import { Share2, Link, Twitter, Facebook } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/hooks/use-toast";

interface SharePostProps {
    title: string;
    url?: string;
}

export function SharePost({ title, url }: SharePostProps) {
    const { toast } = useToast();
    const shareUrl = url || (typeof window !== "undefined" ? window.location.href : "");

    // Native share removed as it was unused in UI

    const handleCopyLink = () => {
        navigator.clipboard.writeText(shareUrl);
        toast({
            title: "Bağlantı kopyalandı",
            description: "Blog yazısı bağlantısı panoya kopyalandı.",
        });
    };

    const shareOnTwitter = () => {
        window.open(
            `https://twitter.com/intent/tweet?text=${encodeURIComponent(title)}&url=${encodeURIComponent(shareUrl)}`,
            "_blank"
        );
    };

    const shareOnFacebook = () => {
        window.open(
            `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
            "_blank"
        );
    };

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                    <Share2 className="mr-2 h-4 w-4" />
                    Paylaş
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleCopyLink}>
                    <Link className="mr-2 h-4 w-4" />
                    Bağlantıyı Kopyala
                </DropdownMenuItem>
                <DropdownMenuItem onClick={shareOnTwitter}>
                    <Twitter className="mr-2 h-4 w-4" />
                    Twitter&apos;da Paylaş
                </DropdownMenuItem>
                <DropdownMenuItem onClick={shareOnFacebook}>
                    <Facebook className="mr-2 h-4 w-4" />
                    Facebook&apos;ta Paylaş
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
