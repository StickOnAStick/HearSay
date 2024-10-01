import multiprocessing
from loguru import logger
from multiprocessing import Process
from lib.Scrapper.yelp.scrapper import YelpScrapper

def run_scrapper(query: str) -> int:
    try:
        scrapper = YelpScrapper(query, location="San Jose, CA")
        status = scrapper.run()
        logger.info(f"Process finished with status: {status}")
        return status
    except Exception as e:
        logger.error(f"There was an error excuting a scrapper process! {e}")
    

if __name__ == "__main__":
    search_querys: list[str] = ["Restaurants"]

    processes: list[Process] = []
    for query in search_querys:
        p: Process = multiprocessing.Process(target=run_scrapper, args=(query,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    logger.debug("All scraper instances have completed.")

