"""
Custom admin forms for Gastrotech catalog.

Provides enhanced forms for media upload with validation.
"""

import hashlib
import io

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Media


class MediaAdminForm(forms.ModelForm):
    """
    Custom admin form for Media that handles file uploads.
    
    - Accepts file upload via FileField
    - Auto-populates bytes, filename, content_type, size_bytes, checksum
    - Extracts image dimensions using Pillow
    - Auto-detects kind based on content_type
    - Validates file size against MAX_MEDIA_UPLOAD_BYTES
    """
    
    upload = forms.FileField(
        required=False,
        help_text="Upload a file (image, PDF, or video). Required for new media.",
    )
    
    class Meta:
        model = Media
        fields = [
            "upload",
            "kind",
            "filename",
            "content_type",
            "width",
            "height",
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make upload required for new objects
        if not self.instance.pk:
            self.fields["upload"].required = True
            self.fields["filename"].required = False
            self.fields["content_type"].required = False
        
        # Make these fields optional since they'll be auto-populated
        self.fields["kind"].required = False
        self.fields["filename"].required = False
        self.fields["content_type"].required = False
    
    def clean_upload(self):
        """Validate uploaded file size."""
        upload = self.cleaned_data.get("upload")
        
        if upload:
            max_size = getattr(settings, "MAX_MEDIA_UPLOAD_BYTES", 10 * 1024 * 1024)
            if upload.size > max_size:
                max_mb = max_size / (1024 * 1024)
                raise ValidationError(
                    f"File too large. Maximum size is {max_mb:.1f} MB. "
                    f"Uploaded file is {upload.size / (1024 * 1024):.1f} MB."
                )
        
        return upload
    
    def clean(self):
        """Process uploaded file and populate model fields."""
        cleaned_data = super().clean()
        upload = cleaned_data.get("upload")
        
        if upload:
            # Read file content
            file_content = upload.read()
            upload.seek(0)  # Reset file pointer
            
            # Auto-populate fields
            cleaned_data["bytes"] = file_content
            cleaned_data["filename"] = upload.name
            cleaned_data["content_type"] = upload.content_type
            cleaned_data["size_bytes"] = len(file_content)
            cleaned_data["checksum_sha256"] = hashlib.sha256(file_content).hexdigest()
            
            # Auto-detect kind based on content_type
            content_type = upload.content_type or ""
            if content_type.startswith("image/"):
                cleaned_data["kind"] = Media.Kind.IMAGE
                # Try to extract image dimensions
                self._extract_image_dimensions(file_content, cleaned_data)
            elif content_type == "application/pdf":
                cleaned_data["kind"] = Media.Kind.PDF
            elif content_type.startswith("video/"):
                cleaned_data["kind"] = Media.Kind.VIDEO
            else:
                # Default to image if unknown
                cleaned_data["kind"] = Media.Kind.IMAGE
        
        return cleaned_data
    
    def _extract_image_dimensions(self, file_content, cleaned_data):
        """Extract image dimensions using Pillow."""
        try:
            from PIL import Image
            
            image = Image.open(io.BytesIO(file_content))
            cleaned_data["width"] = image.width
            cleaned_data["height"] = image.height
        except Exception:
            # If Pillow can't open the image, leave dimensions as None
            pass
    
    def save(self, commit=True):
        """Save the model with processed file data."""
        instance = super().save(commit=False)
        
        # Apply file data from cleaned_data
        if "bytes" in self.cleaned_data:
            instance.bytes = self.cleaned_data["bytes"]
        if "filename" in self.cleaned_data:
            instance.filename = self.cleaned_data["filename"]
        if "content_type" in self.cleaned_data:
            instance.content_type = self.cleaned_data["content_type"]
        if "size_bytes" in self.cleaned_data:
            instance.size_bytes = self.cleaned_data["size_bytes"]
        if "checksum_sha256" in self.cleaned_data:
            instance.checksum_sha256 = self.cleaned_data["checksum_sha256"]
        if "kind" in self.cleaned_data and self.cleaned_data["kind"]:
            instance.kind = self.cleaned_data["kind"]
        if "width" in self.cleaned_data and self.cleaned_data["width"]:
            instance.width = self.cleaned_data["width"]
        if "height" in self.cleaned_data and self.cleaned_data["height"]:
            instance.height = self.cleaned_data["height"]
        
        if commit:
            instance.save()
        
        return instance
