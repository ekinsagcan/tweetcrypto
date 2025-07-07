import tweepy
import requests
import json
import time
import re
from datetime import datetime, timedelta
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ElonPumpBot:
    def __init__(self, twitter_bearer_token, pumpfun_api_key, wallet_private_key):
        """
        Bot initialization
        """
        self.twitter_bearer_token = twitter_bearer_token
        self.pumpfun_api_key = pumpfun_api_key
        self.wallet_private_key = wallet_private_key
        
        # Twitter API client
        self.twitter_client = tweepy.Client(bearer_token=twitter_bearer_token)
        
        # Elon Musk'ın Twitter user ID'si
        self.elon_user_id = "44196397"
        
        # Son kontrol edilen tweet ID'si
        self.last_tweet_id = None
        
        # İşlenmiş tweet'leri saklamak için
        self.processed_tweets = set()
        
        # Pump.fun API base URL
        self.pumpfun_base_url = "https://pumpportal.fun/api"
        
    def get_latest_tweets(self, max_results=10):
        """
        Elon Musk'ın son tweet'lerini getir
        """
        try:
            tweets = self.twitter_client.get_users_tweets(
                id=self.elon_user_id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics', 'text'],
                since_id=self.last_tweet_id
            )
            
            if tweets.data:
                self.last_tweet_id = tweets.data[0].id
                return tweets.data
            return []
            
        except Exception as e:
            logger.error(f"Tweet getirme hatası: {e}")
            return []
    
    def analyze_tweet(self, tweet_text):
        """
        Tweet'i analiz et ve coin oluşturma kriterlerini kontrol et
        """
        # Kripto ile ilgili anahtar kelimeler
        crypto_keywords = [
            'bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'cryptocurrency',
            'blockchain', 'coin', 'token', 'doge', 'dogecoin', 'hodl',
            'moon', 'diamond', 'hands', 'ape', 'defi', 'web3', 'nft'
        ]
        
        # Meme coin potansiyeli olan kelimeler
        meme_keywords = [
            'dog', 'cat', 'moon', 'rocket', 'fire', 'diamond',
            'golden', 'magic', 'super', 'mega', 'ultra', 'crazy'
        ]
        
        tweet_lower = tweet_text.lower()
        
        # Kripto ile ilgili mi?
        crypto_related = any(keyword in tweet_lower for keyword in crypto_keywords)
        
        # Meme potansiyeli var mı?
        meme_potential = any(keyword in tweet_lower for keyword in meme_keywords)
        
        # Emoji sayısı (viral potansiyel)
        emoji_count = len(re.findall(r'[😀-🙏🌀-🗿🚀-🛿⚡-➿]', tweet_text))
        
        # Skor hesaplama
        score = 0
        if crypto_related:
            score += 5
        if meme_potential:
            score += 3
        if emoji_count > 0:
            score += min(emoji_count, 3)
        
        # Büyük harf kullanımı (heyecan göstergesi)
        if any(word.isupper() and len(word) > 2 for word in tweet_text.split()):
            score += 2
            
        return {
            'should_create_coin': score >= 5,
            'score': score,
            'crypto_related': crypto_related,
            'meme_potential': meme_potential,
            'emoji_count': emoji_count
        }
    
    def generate_coin_name(self, tweet_text):
        """
        Tweet'e göre coin ismi oluştur
        """
        # Tweet'ten önemli kelimeleri çıkar
        words = re.findall(r'\b[A-Za-z]+\b', tweet_text)
        
        # Yaygın kelimeleri filtrele
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'will', 'would', 'could', 'should'}
        important_words = [word for word in words if word.lower() not in common_words and len(word) > 2]
        
        if important_words:
            # İlk önemli kelimeyi al ve "Coin" ekle
            base_name = important_words[0].capitalize()
            coin_name = f"{base_name}Coin"
        else:
            # Fallback: timestamp bazlı
            timestamp = datetime.now().strftime("%H%M")
            coin_name = f"ElonCoin{timestamp}"
            
        return coin_name
    
    def create_coin_on_pumpfun(self, coin_name, tweet_text, tweet_url):
        """
        Pump.fun'da coin oluştur
        """
        try:
            # Coin metadatası hazırla
            coin_metadata = {
                "name": coin_name,
                "symbol": coin_name[:6].upper(),
                "description": f"Inspired by Elon Musk's tweet: {tweet_text[:100]}...",
                "telegram": "",
                "twitter": "",
                "website": tweet_url,
                "file": None  # Logo dosyası yoksa null
            }
            
            # Pump.fun API'ye coin oluşturma isteği
            headers = {
                "Authorization": f"Bearer {self.pumpfun_api_key}",
                "Content-Type": "application/json"
            }
            
            # NOT: Bu gerçek pump.fun API endpoint'i değil, örnek amaçlı
            # Gerçek API dokümantasyonunu kontrol etmelisiniz
            response = requests.post(
                f"{self.pumpfun_base_url}/coins/create",
                json=coin_metadata,
                headers=headers
            )
            
            if response.status_code == 200:
                coin_data = response.json()
                logger.info(f"Coin başarıyla oluşturuldu: {coin_data}")
                return coin_data
            else:
                logger.error(f"Coin oluşturma hatası: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Coin oluşturma hatası: {e}")
            return None
    
    def run(self):
        """
        Ana bot döngüsü
        """
        logger.info("Bot başlatılıyor...")
        
        while True:
            try:
                # Son tweet'leri getir
                tweets = self.get_latest_tweets()
                
                for tweet in tweets:
                    if tweet.id not in self.processed_tweets:
                        logger.info(f"Yeni tweet analiz ediliyor: {tweet.text[:50]}...")
                        
                        # Tweet'i analiz et
                        analysis = self.analyze_tweet(tweet.text)
                        
                        if analysis['should_create_coin']:
                            logger.info(f"Coin oluşturma kriteri karşılandı! Skor: {analysis['score']}")
                            
                            # Coin ismini oluştur
                            coin_name = self.generate_coin_name(tweet.text)
                            
                            # Tweet URL'sini oluştur
                            tweet_url = f"https://twitter.com/elonmusk/status/{tweet.id}"
                            
                            # Coin oluştur
                            coin_result = self.create_coin_on_pumpfun(
                                coin_name, 
                                tweet.text, 
                                tweet_url
                            )
                            
                            if coin_result:
                                logger.info(f"✅ Coin oluşturuldu: {coin_name}")
                            else:
                                logger.error(f"❌ Coin oluşturulamadı: {coin_name}")
                        
                        else:
                            logger.info(f"Coin oluşturma kriteri karşılanmadı. Skor: {analysis['score']}")
                        
                        # İşlenmiş tweet'leri kaydet
                        self.processed_tweets.add(tweet.id)
                
                # 60 saniye bekle
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Ana döngü hatası: {e}")
                time.sleep(60)

def main():
    """
    Bot'u başlat
    """
    # API anahtarlarını buraya girin
    TWITTER_BEARER_TOKEN = "your_twitter_bearer_token_here"
    PUMPFUN_API_KEY = "your_pumpfun_api_key_here"
    WALLET_PRIVATE_KEY = "your_wallet_private_key_here"
    
    # Bot'u başlat
    bot = ElonPumpBot(
        twitter_bearer_token=TWITTER_BEARER_TOKEN,
        pumpfun_api_key=PUMPFUN_API_KEY,
        wallet_private_key=WALLET_PRIVATE_KEY
    )
    
    # Bot'u çalıştır
    bot.run()

if __name__ == "__main__":
    main()