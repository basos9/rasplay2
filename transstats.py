import transmission_rpc

class TRA():
    def __init__(self, host, port, user, passw):
        print(f"TRA init {user}@{host}:{port}")
        self.client = transmission_rpc.Client(host=host, port=port, username=user, password=passw)

    def getStats(self):
        # Get stats summary
        lines = list()
        try:
            stats = self.client.session_stats()
            cs = stats.cumulative_stats
            lines.append (f"Tr r/t: {stats.download_speed/1024/1024:.2f} / {stats.upload_speed/1024/1024:.2f} MB/s")
            lines.append (f"  Active: {stats.active_torrent_count} / {stats.torrent_count}")
            lines.append (f"  d/u: {cs.downloaded_bytes/1024/1024/1024:.2f} / {cs.uploaded_bytes/1024/1024/1024:.2f} GB")
        except Exception as e:
            print(f"Exception on transmission getStats "+str(e))
            lines.append("* Transmission ERROR")
            lines.append(str(e))
        return lines

# # Get all torrents
# torrents = client.get_torrents()
# for torrent in torrents:
#     print(f"Name: {torrent.name}")
#     print(f"Status: {torrent.status}")  # 'downloading', 'seeding', 'stopped', etc.
#     print(f"Progress: {torrent.progress:.1f}%")
#     print(f"Download speed: {torrent.rate_download} B/s")
#     print(f"Upload speed: {torrent.rate_upload} B/s")
#     print(f"Downloaded: {torrent.downloaded_ever} bytes")
#     print(f"Uploaded: {torrent.uploaded_ever} bytes")
#     print(f"Seeders: {torrent.seeders}, Leechers: {torrent.leechers}")
#     print("---")
