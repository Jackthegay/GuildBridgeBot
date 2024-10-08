from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import re

@dataclass
class GuildMember:
    name: str
    rank: Optional[str] = None
    experience: Optional[int] = None

@dataclass
class GuildRole:
    name: str
    members: List[GuildMember]

@dataclass
class TopEntry:
    member: GuildMember
    experience: int
    position: int

class GuildMessageParser:
    def __init__(self, message: str):
        self.raw_message = message
        self.guild_name = ""
        self.total_members = 0
        self.online_members = 0
        self.offline_members = 0
        self.roles = []
        self.top_entries = []
        self.date = None
        
    def parse(self) -> str:
        # Determine message type and parse accordingly
        if "Top Guild Experience" in self.raw_message:
            return self._parse_top_message()
        elif "Total Members:" in self.raw_message:
            if "Offline Members:" in self.raw_message:
                return self._parse_online_message()
            else:
                return self._parse_list_message()

    def _extract_member_info(self, member_text: str) -> GuildMember:
        # Remove the bullet point
        member_text = member_text.replace('●', '').strip()
        
        # Extract rank if present
        rank_match = re.match(r'\[(MVP\+?+?|VIP\+?)\]\s+', member_text)
        if rank_match:
            rank = rank_match.group(0).strip('[]')
            name = member_text[rank_match.end():].strip()
            return GuildMember(name=name, rank=rank)
        return GuildMember(name=member_text)

    def _parse_list_message(self) -> str:
        lines = self.raw_message.split('\n')
        current_role = None
        current_members = []

        for line in lines:
            line = line.strip()
            
            if line.startswith('Guild Name:'):
                self.guild_name = line.replace('Guild Name:', '').strip()
                continue
                
            if line.startswith('--') and line.endswith('--'):
                if current_role:
                    self.roles.append(GuildRole(current_role, current_members))
                    current_members = []
                current_role = line.strip('- ')
                continue
                
            if '●' in line:
                # Split by bullet points and process each member
                members = line.split('●')
                for member in members:
                    if member.strip():
                        current_members.append(self._extract_member_info(member))
                        
            if line.startswith('Total Members:'):
                self.total_members = int(re.search(r'\d+', line).group())
            elif line.startswith('Online Members:'):
                self.online_members = int(re.search(r'\d+', line).group())

        # Add the last role if exists
        if current_role:
            self.roles.append(GuildRole(current_role, current_members))

        return self._format_list_embed()

    def _parse_online_message(self) -> str:
        self._parse_list_message()  # Reuse list parsing logic
        # Extract offline members
        for line in self.raw_message.split('\n'):
            if line.startswith('Offline Members:'):
                self.offline_members = int(re.search(r'\d+', line).group())
                break
        return self._format_online_embed()

    def _parse_top_message(self) -> str:
        lines = self.raw_message.split('\n')
        
        # Extract date
        date_line = lines[0]
        date_match = re.search(r'\d{2}/\d{2}/\d{4}', date_line)
        if date_match:
            self.date = datetime.strptime(date_match.group(), '%m/%d/%Y')

        # Parse top entries
        for line in lines[1:]:  # Skip header
            if not line.strip():
                continue
                
            match = re.match(r'(\d+)\.\s+(.+?)\s+(\d+,?\d*)\s+Guild Experience', line)
            if match:
                position = int(match.group(1))
                member_text = match.group(2)
                experience = int(match.group(3).replace(',', ''))
                
                member = self._extract_member_info(member_text)
                member.experience = experience
                self.top_entries.append(TopEntry(member, experience, position))

        return self._format_top_embed()

    def _format_list_embed(self) -> str:
        description = []
        for role in self.roles:
            description.append(f"**{role.name}**")
            member_texts = []
            for member in role.members:
                text = f"[{member.rank}] {member.name}" if member.rank else member.name
                member_texts.append(text)
            description.append(", ".join(member_texts))
            description.append("")  # Empty line for spacing
        
        description.append(f"Total Members: {self.total_members}")
        description.append(f"Online Members: {self.online_members}")
        
        return "\n".join(description).replace("*", "\\*")

    def _format_online_embed(self) -> str:
        description = self._format_list_embed()
        return f"{description}\nOffline Members: {self.offline_members}"

    def _format_top_embed(self) -> str:
        description = [f"Top Guild Experience - {self.date.strftime('%m/%d/%Y')} (today)\n"]
        
        for entry in self.top_entries:
            member = entry.member
            member_text = f"[{member.rank}] {member.name}" if member.rank else member.name
            description.append(
                f"{entry.position}. {member_text} - {entry.experience:,} Guild Experience"
            )
            
        return "\n".join(description).replace("*", "\\*")