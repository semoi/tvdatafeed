import threading, queue, logging

logger = logging.getLogger(__name__)

class Consumer(threading.Thread):
    '''
    Seis data consumer and processor

    This object contains reference to Seis and callback function
    which will be called when new data bar becomes available for
    that Seis. Data reception and calling callback function is
    done in a separate thread which the user must start by calling
    start() method.

    Parameters
    ----------
    seis : Seis
        Consumer receives data bar from this Seis
    callback : func
        reference to a function to be called when new data available,
        function protoype must be func_name(seis, data)

    Methods
    -------
    put(data)
        Put new data into buffer to be processed
    del_consumer()
        Shutdown the callback thread and remove from Seis
    start()
        start data processing and callback thread
    stop()
        Stop the data processing and callback thread
    '''
    def __init__(self, seis, callback):
        super().__init__()

        self._buffer=queue.Queue()
        self._lock = threading.Lock()  # Lock for thread-safe access to attributes
        self._stopped = False  # Flag to indicate if consumer is stopped
        self._seis=seis
        self._callback=callback
        # Use getattr for robustness with mock objects
        callback_name = getattr(self._callback, '__name__', 'callback')
        self.name=callback_name+"_"+self._seis.symbol+"_"+seis.exchange+"_"+seis.interval.value
    
    @property
    def seis(self):
        '''Thread-safe access to seis reference'''
        with self._lock:
            return self._seis

    @seis.setter
    def seis(self, value):
        '''Thread-safe setter for seis reference'''
        with self._lock:
            self._seis = value

    @property
    def callback(self):
        '''Thread-safe access to callback reference'''
        with self._lock:
            return self._callback

    @callback.setter
    def callback(self, value):
        '''Thread-safe setter for callback reference'''
        with self._lock:
            self._callback = value

    def __repr__(self):
        seis = self.seis
        callback = self.callback
        if seis is None or callback is None:
            return f'Consumer(stopped)'
        callback_name = getattr(callback, '__name__', 'callback')
        return f'Consumer({repr(seis)},{callback_name})'

    def __str__(self):
        seis = self.seis
        callback = self.callback
        if seis is None or callback is None:
            return 'Consumer(stopped)'
        callback_name = getattr(callback, '__name__', 'callback')
        return f'{repr(seis)},callback={callback_name}'

    def run(self):
        # callback thread tasks
        try:
            while True:
                # Check if stopped before waiting
                with self._lock:
                    if self._stopped:
                        break

                try:
                    # Use timeout to allow periodic check of stopped flag
                    data = self._buffer.get(timeout=1.0)
                except queue.Empty:
                    continue  # Check stopped flag again

                if data is None:
                    break

                # Get references under lock to ensure thread-safety
                with self._lock:
                    seis = self._seis
                    callback = self._callback

                if seis is None or callback is None:
                    break

                try: # in case user provided function throws an exception
                    callback(seis, data)
                except Exception as e: # remove the consumer from Seis and close down gracefully
                    logger.error(f"Exception in consumer callback: {e}")
                    try:
                        self.del_consumer()
                    except Exception as del_error:
                        logger.warning(f"Error during consumer cleanup: {del_error}")
                    break
        finally:
            # Clean up references
            with self._lock:
                self._seis = None
                self._callback = None
                self._stopped = True
    
    def put(self, data):
        '''
        Put new data into buffer to be processed

        Parameters
        ----------
        data : pandas.DataFrame
            contains single bar data retrieved from TradingView
        '''
        with self._lock:
            if self._stopped:
                return  # Don't put data if consumer is stopped
        try:
            self._buffer.put(data, timeout=5.0)
        except queue.Full:
            logger.warning(f"Consumer buffer full, dropping data for {self.name}")

    def del_consumer(self, timeout=-1):
        '''
        Stop the callback thread and remove from Seis

        Parameters
        ----------
        timeout : int, optional
            maximum time to wait in seconds for return, default
            is -1 (blocking)

        Returns
        -------
        boolean
            True if successful, False if timed out.
        '''
        seis = self.seis
        if seis is None:
            return True  # Already cleaned up
        return seis.del_consumer(self, timeout)

    def stop(self):
        '''
        Stop the data processing and callback thread
        '''
        with self._lock:
            if self._stopped:
                return  # Already stopped
            self._stopped = True

        # Put None to signal shutdown - use non-blocking to avoid deadlock
        try:
            self._buffer.put(None, timeout=1.0)
        except queue.Full:
            pass  # Thread will check _stopped flag anyway
        