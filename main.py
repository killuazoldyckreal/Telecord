if __name__ == "__main__":
    # Run the bots
    try:
        loop = asyncio.get_event_loop()
        
        # Initialize the bot class
        telecord = Telecord()

        # Start the bot
        asyncio.gather(telecord.dcstart(), telecord.tgstart())
        loop.run_forever()
    except:
        traceback.print_exc()
