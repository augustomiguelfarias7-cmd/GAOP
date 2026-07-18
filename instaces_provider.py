"""
GAOP - Instances Provider
Plug-in para descobrir, validar e atualizar automaticamente a lista de instâncias SearXNG.

Gera um instances.json atualizado com as instâncias que estão realmente online.
Execute: python instances_provider.py
"""

import requests
import json
import time
import concurrent.futures
from typing import List, Tuple, Dict
from urllib.parse import urlparse


class InstancesProvider:
    """
    Gerencia uma lista grande de instâncias SearXNG públicas conhecidas.
    Faz health check automático e gera um instances.json com as que estão online.
    """

    # Lista completa de instâncias SearXNG públicas conhecidas
    KNOWN_INSTANCES = [
        # Instâncias oficiais e bem conhecidas
        "https://searx.be",
        "https://search.sapti.me",
        "https://searx.tiekoetter.com",
        "https://priv.au",
        "https://searx.work",
        
        # Mais instâncias públicas da comunidade
        "https://baresearch.org",
        "https://opnxng.com",
        "https://searx.namejeff.xyz",
        "https://search.privacyguardian.org",
        "https://searx.pimux.de",
        "https://search.4get.ca",
        "https://searx.0x3d.systems",
        "https://search.nextcloud.com",
        "https://searx.protoolio.de",
        "https://search.snopyta.org",
        "https://searx.spb.ru",
        "https://searx.de",
        "https://search.disroot.org",
        "https://searx.privacydev.net",
        "https://search.privacy-hangar.org",
        "https://searxng.instaclustr.com",
        "https://searx.awebstudio.com",
        "https://searx.ca",
        "https://search.mdosch.de",
        "https://metasearch.privacyguardian.net",
        "https://search.eoarg.com",
        "https://searx.digitalcourage.de",
        "https://search.ngocn2.org",
        "https://searx.org",
        "https://search.d200.de",
        "https://www.searx.ir",
        "https://searx.anongoth.pl",
        "https://searx.evozi.com",
        "https://search.hyperbola.info",
        "https://searxng.heimdall.site",
        "https://searx.semipheus.com",
        "https://search.maeve.dev",
        "https://search.ourselfhosted.net",
        "https://searx.nohost.me",
        "https://search.privacydev.net",
        "https://searxng.heimdall.site",
        "https://searx.semipheus.com",
        "https://search.maeve.dev",
        "https://searx.me",
        "https://search.mwzt.de",
        "https://search.earthend.cloud",
        "https://search.asciimov.net",
        "https://searx.silentknight.com",
        "https://search.wires.digital",
        "https://searx.bouncepaw.com",
        "https://search.visionary.cloud",
        "https://searx.callan.io",
    ]

    # Instâncias de backup conhecidas
    BACKUP_INSTANCES = [
        "https://baresearch.org",
        "https://opnxng.com",
        "https://searx.namejeff.xyz",
        "https://search.privacyguardian.org",
        "https://searx.pimux.de",
        "https://search.disroot.org",
        "https://searx.ca",
        "https://searx.digitalcourage.de",
    ]

    def __init__(self, timeout: float = 5.0, workers: int = 30):
        self.timeout = timeout
        self.workers = workers
        self.online_instances: List[str] = []
        self.offline_instances: List[str] = []

    def _check_instance(self, url: str) -> Tuple[str, bool]:
        """Verifica se uma instância está online."""
        try:
            normalized = url.replace("://www.", "://").rstrip("/")
            
            resp = requests.get(
                normalized,
                timeout=self.timeout,
                headers={"User-Agent": "GAOP-InstanceProvider/1.0"},
                allow_redirects=True,
            )
            
            is_online = resp.status_code < 500
            return normalized, is_online
        except Exception:
            return url, False

    def check_all(self, instances: List[str] = None) -> None:
        """Verifica todas as instâncias em paralelo."""
        if instances is None:
            instances = self.KNOWN_INSTANCES

        print(f"\n🔍 Verificando {len(instances)} instâncias SearXNG...")
        print(f"⏱️  Timeout: {self.timeout}s | Workers: {self.workers}\n")

        self.online_instances = []
        self.offline_instances = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(self._check_instance, url): url for url in instances}
            completed = 0

            for future in concurrent.futures.as_completed(futures):
                url, is_online = future.result()
                if is_online:
                    self.online_instances.append(url)
                    print(f"✅ {url}")
                else:
                    self.offline_instances.append(url)
                    print(f"❌ {url}")
                completed += 1
                if completed % 10 == 0:
                    print(f"   [{completed}/{len(instances)}]\n")

        print(f"\n{'='*60}")
        print(f"📊 Resultado Final:")
        print(f"   ✅ Online: {len(self.online_instances)}")
        print(f"   ❌ Offline: {len(self.offline_instances)}")
        print(f"{'='*60}\n")

    def generate_instances_json(self, output_file: str = "instances.json") -> None:
        """Gera um instances.json com as instâncias online."""
        if not self.online_instances:
            print("⚠️  Nenhuma instância online detectada!")
            return

        primary = [i for i in self.online_instances if i not in self.BACKUP_INSTANCES]
        backup = [i for i in self.online_instances if i in self.BACKUP_INSTANCES]

        if len(backup) < 3:
            primary_backup = primary[:3]
            backup.extend([b for b in primary_backup if b not in backup])

        data = {
            "instances": primary[:200],
            "backup_instances": backup[:50],
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_online": len(self.online_instances),
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✅ Arquivo gerado: {output_file}")
        print(f"   - Instâncias principais: {len(data['instances'])}")
        print(f"   - Instâncias backup: {len(data['backup_instances'])}")
        print(f"   - Gerado em: {data['generated_at']}\n")

    def get_statistics(self) -> Dict:
        """Retorna estatísticas da verificação."""
        total = len(self.online_instances) + len(self.offline_instances)
        return {
            "total_checked": total,
            "online": len(self.online_instances),
            "offline": len(self.offline_instances),
            "uptime_percentage": (len(self.online_instances) / total * 100) if total else 0,
        }


def main():
    """Executa o plug-in de descoberta de instâncias."""
    provider = InstancesProvider(timeout=5.0, workers=30)
    provider.check_all()
    provider.generate_instances_json("instances.json")

    stats = provider.get_statistics()
    print("📈 Estatísticas:")
    print(f"   Total verificado: {stats['total_checked']}")
    print(f"   Online: {stats['online']}")
    print(f"   Offline: {stats['offline']}")
    print(f"   Uptime: {stats['uptime_percentage']:.1f}%\n")

    with open("instances_report.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "statistics": stats,
                "online_instances": provider.online_instances,
                "offline_instances": provider.offline_instances,
                "checked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print("📄 Relatório salvo em: instances_report.json\n")


if __name__ == "__main__":
    main()
