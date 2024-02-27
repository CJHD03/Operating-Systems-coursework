# Student: CJ Delphias
# Date: 2/15/2024

"""
Implements a Thread in the Simulator.

Classes:
    Thread extends SimThread

"""
from Globals import Globals
from Hardware import Timer, CPU
from Memory import MMU
from Interrupts import Interrupt
from MyQueue import PriorityQueue
from SimThreads import SimThread
from SimExceptions import SimException


class Thread(SimThread):
    """ Implements a Thread in the Simulator.

    Attributes:
        Class (Static) Data:
            __readyQueue : PriorityQueue
                 The ready-to-run queue of threads
            __Quantum : int
                 This is an optional field that would be used when implemented Round-Robin

    Functions:
        Class (Static) Functions:
            initThreads(cls)
            scheduler(cls)
            getReadyQueue(cls) -> queue
            snapshot(cls) -> string

        Instance Functions:
            __init__(self, id, task, nonPreemptive) (Constructor)
            kill(self)
            sleep(self)
            wake(self, frame = None)
            getId(self) -> int
            getStatus(self) -> Thread Status
            getTask(self) -> Task
            getNonPreemptive(self) -> boolean
            getPriority(self) -> int
            getKey(self) -> int
            __eq__(self, other) -> boolean
            __ne__(self, other) -> boolean
            __str__(self) -> string

    """
    __readyQueue = None
    __QUANTUM = 100

    @classmethod
    def initThreads(cls):
        """
        This is a class method that is called at boot time to initialize any class data.

        Parameters:
            None

        Returns:
            None
        """

        # 4# This function should:
        #     - Initialize/Instantiate the ready queue
        #     - Register class the scheduler() functions as the interrupt 
        #       handler for the TimerInterrupt interrupt.

        Interrupt.registerHandler(Globals.TimerInterrupt, cls.scheduler)
        cls.__readyQueue = PriorityQueue()

    def __init__(self, id, task, nonPreemptive=False):
        """
        This is the constructor.

        Parameters:
            id: int
            task: Task
            nonPreemptive: boolean (default is False)

        Returns:
            None
        """
        # 20# This function should:
        #     - Call the super class constructor passing the same parameters as arguments.
        #     - Initialize instance data (all should be private) for:
        #         * id
        #         * task
        #         * non-preemptive status
        #         * status (initialized to ThreadNew)
        #         * priority (initialized to be the same as the task's priority)
        #     - Set the thread's status to ThreadReady
        #     - Enqueue the thread into the ready queue
        super().__init__(id, task, nonPreemptive)
        self.__id = id
        self.__task = task
        self.__status = Globals.ThreadNew
        self.__nonPreemptive = nonPreemptive
        self.__priority = task.getPriority()
        self.__status = Globals.ThreadReady
        Thread.__readyQueue.enqueue(self)

    def kill(self):
        """
        Kills the thread.

        Parameters:
            None

        Returns:
            None
        """
        # 2g# This function should:
        #     - Call the super class kill() function
        #     - If the thread's status is ThreadRunning, then
        #         * clear the timer (see clearTimer() in the Timer class)
        #         * set the PTBR() to None
        #         (* seting the active thread to none is not necessary since this thread
        #           is being removed.)
        #         * set the rescheduleNeeded flag (see setRescheduleNeeded() in the
        #           Globals class)
        #     - Otherwise, if the thread's status is ThreadReady, remove it from the
        #       ready queue.
        #     - Set the thread's status to ThreadKill
        #     - Remove the thread from the Task's list of threads
        #     - If the status of the *task* is not TaskKill and the number
        #       of threads of the Task has now dropped to zero, kill the task.
        #       (You don't want to kill a task that is already being killed.)
        #       Since this means calling a system call (in priviledge mode) you
        #       have to generate a trap by:
        #         * set the type of interrupt in register 0. The type of interrupt
        #           is TaskKillInterrupt. (See TaskKillInterrupt in the Globals
        #           class and setRegister() in the CPU class.)
        #         * set the task in register 1. (Note that you are actually putting
        #           the address of the task in the register, which works perfectly
        #           fine.)
        #         * call the trap() function in the Interrupt class passing the
        #           interrupt type as a parameter. (See trap() in the Interrupt
        #           class.)

        SimThread.kill(self)
        if self.__status is Globals.ThreadRunning:
            Timer.clearTimer()
            MMU.setPTBR(None)
            Globals.setRescheduleNeeded()
        elif self.__status is Globals.ThreadReady:
            Thread.__readyQueue.remove(self)
        self.__status = Globals.ThreadKill
        self.__task.removeThread(self)

        if self.__task.getStatus() is not Globals.TaskKill and self.__task.getNumThreads() <= 0:
            CPU.setRegister(0, Globals.TaskKillInterrupt)
            CPU.setRegister(1, self.__task)
            Interrupt.trap(Globals.TaskKillInterrupt)

    def sleep(self):
        """
        Puts a thread to sleep (or puts it in a waiting state).

        Parameters:
            None

        Returns:
            None
        """

        # ni# This function should:
        #     - Call the super class sleep() function
        #     - If the thread's status is ThreadRunning, then
        #         * clear the timer (see clearTimer() in the Timer class)
        #         * set the PTBR() to None
        #         * set the active thread of the task to None
        #         * set the threads status to ThreadWaiting
        #         * set the rescheduleNeeded flag (see setRescheduleNeeded() in the
        #           Globals class)
        #     - Otherwise, if the thread's status is ThreadReady, then
        #         * remove it from the ready queue
        #         * set the thread's status to ThreadWaiting
        #     - Otherwise (the thread's status is ThreadWaiting), then
        #       increment its status by one (since waiting is actually a counter)
        SimThread.sleep(self)
        if self.__status is Globals.ThreadRunning:
            Timer.clearTimer()
            MMU.setPTBR(None)
            self.__task.setActiveThread(None)
            self.__status = Globals.ThreadWaiting
            Globals.setRescheduleNeeded()
        elif self.__status is Globals.ThreadReady:
            Thread.__readyQueue.remove(self)
            self.__status = Globals.ThreadWaiting
        else:
            self.__status += 1

    def wake(self, frame=None):
        """
        Wakes up a thread, although it may only decrement the waiting counter leaving
        it still in a waiting state.

        Parameters:
            frame: Frame (default None)

        Returns:
            None
        """

        # r# This function should:
        #     - Call the super class wake() function passing the same parameters as arguments.
        #     - If the thread's priority is less than zero, then it is an
        #       Operating System or Real-time thread with high priority.  You should:
        #         * set its status to ThreadReady
        #         * enqueue it into the ready queue
        #         * set the rescheduleNeeded flag (see setRescheduleNeeded() in the
        #           Globals class)
        #     - Otherwise, if the thread's status is less than or equal to
        #       ThreadWaiting, then
        #         * set its status to ThreadReady
        #         * enqueue it into the ready queue
        #         * set the rescheduleNeeded flag (see setRescheduleNeeded() in the
        #           Globals class)
        #     - Otherwise, (the thread is still in a nested waiting state), then
        #         * decrement its status
        SimThread.wake(self, frame)
        if self.__priority < 0:
            self.__status = Globals.ThreadReady
            Thread.__readyQueue.enqueue(self)
            Globals.setRescheduleNeeded()
        elif self.__priority <= Globals.ThreadWaiting:
            self.__status = Globals.ThreadReady
            Thread.__readyQueue.enqueue(self)
            Globals.setRescheduleNeeded()
        else:
            self.__status -= 1

    @classmethod
    def scheduler(cls):
        """
        This is the scheduler.  Its job is to decide which thread should run next.
        It is also the handler for the timer interrupt. The scheduler should be
        called whenever there is an "opportunity" to reschedule. An "opportunity" is:
            - The timer interrupt occurs
            - A new thread is created
            - A thread is added to the queue because:
               + a new thread was create
               + a thread was woken
            - The current running thread has stopped because:
               + it was killed or terminated
               + it is put to sleep
        There is a Global flag (see Globals.setRescheduleNeeded()) that indicates
        there is an "opportunity" to reschedule, which will invoke the scheduler.
        The reason that flag should be used instead of just calling the scheduler
        is because a system call or interrupt handler must complete its work before
        the scheduler can reschedule.  Therefore, we need to delay that call to the
        scheduler.

        Parameters:
            None

        Returns:
            None
        """

        # p# This function should:
        #     - Make an assertion that the mode is privileged mode. An assertion can be made with
        #       the python keyword "assert" followed by a boolean expression that you expect to be
        #       true. If the boolean expression is not true, then an AssertionException is raised.
        #       You need to assert that the mode is in privileged mode. See the getMode() function in
        #       the Globals class as well as the PrivilegedMode constant.
        #     - If the PTBR is not None AND
        #              the task from the PTBR is not None AND
        #              the active thread of the task from the PTBR is not None, then
        #         * Get the task from the PTBR
        #         * Get the active thread from the task
        #         * If the thread is non-preemptive, then return (i.e. let it keep running)
        #             + Set the mode back to user mode (see setUserMode() in the Globals
        #               class) and return
        #         * Get the thread at the front of the queue (but don't
        #           remove it, i.e. use peek()).
        #         * Get the interrupt type from register 0 (see getRegister() in the CPU class)
        #         * If the interrupt type is TimerInterrupt OR
        #              (the thread at the front of the queue is not None AND it has higher
        #              priority that the current running thread), then preempt the current
        #              running thread by doing:
        #             + set the active thread's status to ThreadReady
        #             + enqueue the active thread into the ready queue
        #             + clear the timer
        #             + set the PTBR to None
        #         * Otherwise, just return to let the current thread continue by:
        #             + Set the mode back to user mode (see setUserMode() in the Globals
        #               class) and return
        #
        #     - If the PTBR is None (because the CPU was idle to begin with or you just
        #       preempted the current thread above), then:
        #         * If the queue is not empty:
        #             + Dequeue the next thread
        #             + Get the task of the next thread
        #             + Set the active thread of that task to this new thread
        #             + Set the thread status to ThreadRunning
        #             + Set the PTBR to point to the PageTable of the thread's task (see
        #               (setPTBR() of the MMU class and getPageTable() of the Task class)
        #             + Clear the timer just to make sure
        #             + If you are implementing Round-Robin, then set the timer to go
        #                 off after Quantum amount of time
        #     - Set the mode back to user mode (see setUserMode() in the Globals
        #       class) and return

        assert Globals.getMode() == Globals.PrivilegedMode
        ptbr = MMU.getPTBR()

        if MMU.getPTBR() is not None and ptbr.getTask() is not None and ptbr.getTask().getActiveThread() is not None:
            ptbr_task = MMU.getPTBR().getTask()
            ptbr_active_thread = ptbr_task.getActiveThread()
            if ptbr_active_thread.getNonPreemptive():
                Globals.setUserMode()
                return
            nextInQueue = Thread.__readyQueue.peek()
            interruptType = CPU.getRegister(0)
            if (interruptType is Globals.TimerInterrupt or nextInQueue is not None and nextInQueue.getPriority() >
                    ptbr_active_thread.getPriority()):
                ptbr_active_thread.__status = Globals.ThreadReady
                Thread.__readyQueue.enqueue(ptbr_active_thread)
                Timer.clearTimer()
                MMU.setPTBR(None)
        else:
            Globals.setUserMode()

        if MMU.getPTBR() is None:
            if not (Thread.__readyQueue.isEmpty()):
                dequeuedThread = Thread.__readyQueue.dequeue()
                dequeuedThreadTask = dequeuedThread.getTask()
                dequeuedThreadTask.setActiveThread(dequeuedThread)

                dequeuedThread.__status = Globals.ThreadRunning

                MMU.setPTBR(dequeuedThreadTask.getPageTable())
                Timer.clearTimer()
                Timer.setTimer(Thread.__QUANTUM)
        Globals.setUserMode()

    def getId(self):
        """
        Gets the thread's id.

        Parameters:
            None

        Returns:
            id: int
        """
        return self.__id

    def getStatus(self):
        """
        Gets the thread's status.

        Parameters:
            None

        Returns:
            id: int
        """
        return self.__status

    def getTask(self):
        """
        Gets the thread's task.

        Parameters:
            None

        Returns:
            task: Task
        """
        return self.__task

    def getNonPreemptive(self):
        """
        Gets the thread's non-preemptive status.

        Parameters:
            None

        Returns:
            non-preemptive status: boolean
        """
        return self.__nonPreemptive

    def getPriority(self):
        """
        Gets the thread's priority.

        Parameters:
            None

        Returns:
            priority: int
        """
        return self.__priority

    def getKey(self):
        """
        Gets the thread's key.  The Priority Queue looks specifically for a function
        called "getKey()" that it can call to determine the ordering of values in
        a queue.  Since we will want to use a priority queue where a thread's priority
        is how it should order them, this function simply return the priority of the thread.

        Parameters:
            None

        Returns:
            key: int
        """
        return Thread.__readyQueue.peek().getPriority()

    def __eq__(self, other):
        """
        Determines if two threads are equal based upon their task id's and
        thread id's.

        Parameters:
            self: Thread
            other: Thread

        Returns:
            True if self and other are the same thread, False otherwise.
        """

        # s# Determines if two threads are equal based upon their task id's and
        # thread id's.  Since multiple tasks can have the same thread numbers,
        # it is not sufficient to only check the thread ids.  Task id's are
        # unique in the system, so you need to check both the task id and
        # the thread id to see if they match.

        # DO NOT TRY TO DO return self == other. This will be an infinite loop.
        if self.getId() is other.getId() and self.getTask().getId() is other.getTask().getId():
            return True
        else:
            return False

    def __ne__(self, other):
        """
        Determines if two threads are not equal based upon their task id's and
        thread id's.

        Parameters:
            self: Thread
            other: Thread

        Returns:
            True if self and other are not the same thread, False otherwise.
        """
        # DO NOT TRY TO DO return self != other. This will be an infinite loop.
        if self.getId() is not other.getId() and self.getTask().getId() is not other.getTask().getId():
            return True
        else:
            return False

    def __str__(self):
        """
        Returns a string representation of a thread useful for logging purposes.

        Parameters:
            None

        Returns:
            A string representation of a thread: string
        """
        # Feel free to modify this if you don't like the way threads are printing.

        return "Thread " + str(self.getTask().getId()) + ":" + str(self.getId()) + \
            "(" + self.getPrettyStatus() + " P" + str(self.getPriority()) + ")"

    @classmethod
    def getReadyQueue(cls):
        """
        This returns the Ready-to-run queue.  It's main purpose is to allow the
        Simulator to check the queue for errors.

        Parameters:
            None

        Returns:
            The ready queue: Priority Queue
        """
        return cls.__readyQueue

    @classmethod
    def snapshot(cls):
        """
        Takes a snapshot of the current state of the threads (specifically, the ready queue) and
        returns it as a string (suitable for printing).

        Parameters:
            None

        Returns:
            string
        """
        # Feel free to modify this if you want to see other information during a snapshot.

        result = ""
        readyQ = cls.getReadyQueue()
        result += "Student's Ready Queue = \n" + str(readyQ) + "\n"
        return result
