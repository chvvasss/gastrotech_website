import Link from "next/link";
import Image from "next/image";
import { Container } from "@/components/layout";
import { ArrowLeft, Calendar, User, Clock, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchBlogPost } from "@/lib/api/client";
import { SharePost } from "@/components/blog/share-post";
import { notFound } from "next/navigation";
import { Metadata } from "next";

export const revalidate = 600;

type Props = {
  params: Promise<{ slug: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const post = await fetchBlogPost(slug);
    return {
      title: post.meta_title || post.title || "Blog Detay",
      description: post.meta_description || post.excerpt,
    };
  } catch {
    return {
      title: "Blog Yazısı Bulunamadı",
    };
  }
}

export default async function BlogPostPage({ params }: Props) {
  const { slug } = await params;
  let post;

  try {
    post = await fetchBlogPost(slug);
  } catch {
    notFound();
  }

  return (
    <Container className="py-8 lg:py-12">
      {/* Back Link */}
      <Link
        href="/blog"
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-primary"
      >
        <ArrowLeft className="h-4 w-4" />
        {`Blog'a Dön`}
      </Link>

      <article className="mx-auto max-w-3xl">
        {/* Header */}
        <header className="mb-8">
          {post.category && (
            <Link
              href={`/blog?category=${post.category.slug}`}
              className="inline-block rounded-sm bg-primary/10 px-3 py-1 text-sm font-medium text-primary hover:bg-primary/20 transition-colors"
            >
              {post.category.name_tr}
            </Link>
          )}
          <h1 className="mt-4 text-3xl font-bold lg:text-4xl text-foreground">
            {post.title}
          </h1>
          {post.excerpt && (
            <p className="mt-4 text-lg text-muted-foreground">
              {post.excerpt}
            </p>
          )}
          <div className="mt-6 flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            {post.author_name && (
              <span className="flex items-center gap-1">
                <User className="h-4 w-4" />
                {post.author_name}
              </span>
            )}
            {post.published_at && (
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {new Date(post.published_at).toLocaleDateString("tr-TR", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {post.reading_time_min} dk okuma
            </span>
            <span className="flex items-center gap-1">
              <Eye className="h-4 w-4" />
              {post.view_count} görüntülenme
            </span>
          </div>
        </header>

        {/* Featured Image */}
        {post.cover_url && (
          <div className="relative mb-8 aspect-[16/9] overflow-hidden rounded-sm bg-muted shadow-sm">
            <Image
              src={post.cover_url}
              alt={post.title}
              fill
              className="object-cover"
              sizes="(max-width: 768px) 100vw, (max-width: 1200px) 75vw, 50vw"
              priority
            />
          </div>
        )}

        {/* Content */}
        <div
          className="prose prose-stone max-w-none dark:prose-invert prose-headings:font-bold prose-a:text-primary prose-img:rounded-sm"
          dangerouslySetInnerHTML={{ __html: post.content || "" }}
        />

        {/* Tags */}
        {post.tags && post.tags.length > 0 && (
          <div className="mt-8 flex flex-wrap gap-2">
            {post.tags.map((tag) => (
              <span key={tag.id} className="text-xs bg-muted px-2.5 py-1 rounded-sm text-muted-foreground font-medium">
                #{tag.name}
              </span>
            ))}
          </div>
        )}

        {/* Share */}
        <div className="mt-12 flex items-center justify-between border-t pt-6">
          <span className="text-sm text-muted-foreground">
            Bu yazıyı paylaşın
          </span>
          <div className="flex gap-2">
            <SharePost title={post.title} />
          </div>
        </div>

        {/* Related Posts CTA (Placeholder for now, can be dynamic later) */}
        <div className="mt-12 rounded-sm bg-muted/50 p-8 text-center">
          <h3 className="text-lg font-semibold">Daha Fazla İçerik</h3>
          <p className="mt-2 text-sm text-muted-foreground">
            Blog sayfamızda daha fazla makale ve rehber bulabilirsiniz.
          </p>
          <Button asChild className="mt-4">
            <Link href="/blog">Tüm Yazıları Gör</Link>
          </Button>
        </div>
      </article>
    </Container>
  );
}
