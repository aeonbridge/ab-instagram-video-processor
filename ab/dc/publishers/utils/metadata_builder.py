"""
Metadata Builder Utility
Builds platform-specific metadata for video publishing
"""

import re
from typing import List, Dict, Optional
from pathlib import Path


class MetadataBuilder:
    """Builds optimized metadata for different platforms"""

    # YouTube video categories
    YOUTUBE_CATEGORIES = {
        'film': '1',
        'autos': '2',
        'music': '10',
        'pets': '15',
        'sports': '17',
        'travel': '19',
        'gaming': '20',
        'people': '22',
        'comedy': '23',
        'entertainment': '24',
        'news': '25',
        'howto': '26',
        'education': '27',
        'science': '28',
        'nonprofits': '29',
    }

    # Maximum lengths
    MAX_TITLE_LENGTH = {
        'youtube': 100,
        'tiktok': 150,
    }

    MAX_DESCRIPTION_LENGTH = {
        'youtube': 5000,
        'tiktok': 2200,
    }

    MAX_TAGS = {
        'youtube': 500,  # characters
        'tiktok': 30,    # hashtags
    }

    def __init__(self, platform: str):
        """
        Initialize metadata builder

        Args:
            platform: Platform name ('youtube' or 'tiktok')
        """
        self.platform = platform.lower()

    def build_title(
        self,
        title: str,
        truncate: bool = True,
        add_keywords: Optional[List[str]] = None
    ) -> str:
        """
        Build optimized title for platform

        Args:
            title: Base title
            truncate: If True, truncate to platform limits
            add_keywords: Optional keywords to append

        Returns:
            Optimized title
        """
        # Clean title
        title = self._clean_text(title)

        # Add keywords if provided
        if add_keywords:
            keywords_str = ' | ' + ' | '.join(add_keywords[:3])
            if len(title + keywords_str) <= self.MAX_TITLE_LENGTH[self.platform]:
                title += keywords_str

        # Truncate if needed
        if truncate:
            max_length = self.MAX_TITLE_LENGTH[self.platform]
            if len(title) > max_length:
                title = title[:max_length - 3] + '...'

        return title

    def build_description(
        self,
        description: str,
        hashtags: Optional[List[str]] = None,
        links: Optional[Dict[str, str]] = None,
        call_to_action: Optional[str] = None,
        truncate: bool = True
    ) -> str:
        """
        Build optimized description for platform

        Args:
            description: Base description
            hashtags: Optional list of hashtags
            links: Optional dict of links {'label': 'url'}
            call_to_action: Optional CTA text
            truncate: If True, truncate to platform limits

        Returns:
            Optimized description
        """
        parts = []

        # Main description
        if description:
            parts.append(self._clean_text(description))

        # Add hashtags
        if hashtags:
            formatted_tags = self._format_hashtags(hashtags)
            if formatted_tags:
                parts.append('')  # Empty line
                parts.append(formatted_tags)

        # Add CTA
        if call_to_action:
            parts.append('')
            parts.append(call_to_action)

        # Add links
        if links:
            parts.append('')
            for label, url in links.items():
                parts.append(f"{label}: {url}")

        # Platform-specific formatting
        if self.platform == 'youtube':
            # Add timestamps if description has time markers
            parts = self._add_youtube_timestamps(parts)

        final_description = '\n'.join(parts)

        # Truncate if needed
        if truncate:
            max_length = self.MAX_DESCRIPTION_LENGTH[self.platform]
            if len(final_description) > max_length:
                final_description = final_description[:max_length - 3] + '...'

        return final_description

    def build_tags(
        self,
        tags: List[str],
        auto_tags: bool = True,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> List[str]:
        """
        Build optimized tags for platform

        Args:
            tags: Base tags list
            auto_tags: If True, extract tags from title/description
            title: Optional title for auto-tagging
            description: Optional description for auto-tagging

        Returns:
            Optimized tags list
        """
        all_tags = set()

        # Add provided tags
        for tag in tags:
            cleaned = self._clean_tag(tag)
            if cleaned:
                all_tags.add(cleaned)

        # Auto-extract tags
        if auto_tags:
            if title:
                all_tags.update(self._extract_keywords(title))
            if description:
                all_tags.update(self._extract_keywords(description))

        # Platform-specific filtering
        if self.platform == 'youtube':
            # YouTube tags should be concise
            all_tags = {tag for tag in all_tags if len(tag) <= 30}

            # Check total character count
            tags_str = ','.join(all_tags)
            if len(tags_str) > self.MAX_TAGS['youtube']:
                # Sort by length and take shortest tags first
                all_tags = sorted(all_tags, key=len)
                final_tags = []
                current_length = 0
                for tag in all_tags:
                    if current_length + len(tag) + 1 <= self.MAX_TAGS['youtube']:
                        final_tags.append(tag)
                        current_length += len(tag) + 1
                    else:
                        break
                return final_tags

        elif self.platform == 'tiktok':
            # TikTok has max 30 hashtags
            all_tags = list(all_tags)[:self.MAX_TAGS['tiktok']]

        return list(all_tags)

    def build_youtube_metadata(
        self,
        title: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        category: str = "entertainment",
        privacy: str = "public",
        language: str = "en",
        made_for_kids: bool = False,
        embeddable: bool = True,
        public_stats: bool = True,
        notify_subscribers: bool = True
    ) -> Dict:
        """
        Build complete YouTube metadata

        Args:
            title: Video title
            description: Video description
            tags: Video tags
            category: Category name or ID
            privacy: Privacy status (public/private/unlisted)
            language: Language code
            made_for_kids: If True, mark as made for kids
            embeddable: Allow embedding
            public_stats: Show public statistics
            notify_subscribers: Notify subscribers on publish

        Returns:
            YouTube API metadata dict
        """
        # Get category ID
        category_id = self.YOUTUBE_CATEGORIES.get(category.lower(), category)

        return {
            'snippet': {
                'title': self.build_title(title),
                'description': self.build_description(
                    description,
                    hashtags=tags,
                ),
                'tags': self.build_tags(tags or [], title=title, description=description),
                'categoryId': str(category_id),
                'defaultLanguage': language,
                'defaultAudioLanguage': language,
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': made_for_kids,
                'embeddable': embeddable,
                'publicStatsViewable': public_stats,
            },
            'notifySubscribers': notify_subscribers
        }

    def build_tiktok_metadata(
        self,
        title: str,
        privacy: str = "PUBLIC_TO_EVERYONE",
        disable_duet: bool = False,
        disable_comment: bool = False,
        disable_stitch: bool = False,
        video_cover_timestamp_ms: int = 1000
    ) -> Dict:
        """
        Build complete TikTok metadata

        Args:
            title: Video title/caption
            privacy: Privacy level
            disable_duet: Disable duet feature
            disable_comment: Disable comments
            disable_stitch: Disable stitch feature
            video_cover_timestamp_ms: Thumbnail timestamp

        Returns:
            TikTok API metadata dict
        """
        return {
            'post_info': {
                'title': self.build_title(title),
                'privacy_level': privacy,
                'disable_duet': disable_duet,
                'disable_comment': disable_comment,
                'disable_stitch': disable_stitch,
                'video_cover_timestamp_ms': video_cover_timestamp_ms,
            }
        }

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        return text.strip()

    def _clean_tag(self, tag: str) -> str:
        """Clean and normalize tag"""
        # Remove # if present
        tag = tag.lstrip('#')
        # Remove special characters
        tag = re.sub(r'[^\w\s-]', '', tag)
        # Remove extra spaces
        tag = re.sub(r'\s+', ' ', tag).strip()
        return tag

    def _format_hashtags(self, hashtags: List[str]) -> str:
        """Format hashtags for description"""
        formatted = []
        for tag in hashtags:
            cleaned = self._clean_tag(tag)
            if cleaned:
                # Remove spaces for hashtag format
                tag_no_space = cleaned.replace(' ', '')
                formatted.append(f'#{tag_no_space}')
        return ' '.join(formatted)

    def _extract_keywords(self, text: str, min_length: int = 3) -> set:
        """Extract keywords from text"""
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Split into words
        words = text.split()
        # Filter by length and common words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'this', 'that', 'these', 'those', 'it', 'its', 'as', 'if', 'when',
        }
        keywords = {
            word for word in words
            if len(word) >= min_length and word not in stop_words
        }
        return keywords

    def _add_youtube_timestamps(self, parts: List[str]) -> List[str]:
        """Add YouTube timestamp formatting"""
        # YouTube auto-detects timestamps in format: 0:00 or 00:00
        # This function ensures they're properly formatted
        timestamp_pattern = r'(\d{1,2}):(\d{2})'

        new_parts = []
        for part in parts:
            # Check if part contains timestamps
            if re.search(timestamp_pattern, part):
                # Ensure proper formatting
                part = re.sub(
                    timestamp_pattern,
                    lambda m: f"{int(m.group(1))}:{m.group(2)}",
                    part
                )
            new_parts.append(part)

        return new_parts

    @staticmethod
    def suggest_hashtags_for_niche(niche: str) -> List[str]:
        """Suggest popular hashtags for specific niches"""
        hashtag_suggestions = {
            'gaming': [
                'gaming', 'gamer', 'gameplay', 'videogames', 'gamingcommunity',
                'gaminglife', 'esports', 'streamer', 'twitch', 'youtube'
            ],
            'music': [
                'music', 'musician', 'musicvideo', 'song', 'artist',
                'musicproducer', 'newmusic', 'musiclover', 'instamusic', 'rap'
            ],
            'fitness': [
                'fitness', 'workout', 'gym', 'fitnessmotivation', 'fit',
                'bodybuilding', 'training', 'health', 'fitfam', 'exercise'
            ],
            'food': [
                'food', 'foodie', 'foodporn', 'instafood', 'cooking',
                'recipe', 'delicious', 'foodstagram', 'yummy', 'chef'
            ],
            'travel': [
                'travel', 'traveling', 'travelgram', 'wanderlust', 'adventure',
                'explore', 'vacation', 'instatravel', 'tourism', 'travelphotography'
            ],
            'comedy': [
                'funny', 'comedy', 'memes', 'humor', 'lol',
                'meme', 'funnyvideos', 'laugh', 'jokes', 'viral'
            ],
            'education': [
                'education', 'learning', 'tutorial', 'howto', 'knowledge',
                'teaching', 'study', 'educational', 'school', 'tips'
            ],
        }

        return hashtag_suggestions.get(niche.lower(), [])
