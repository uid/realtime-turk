Retainer Model
==============

Setup
-----

*	**Make a settings.py**

	Look at settings.template.py and make a duplicate, settings.py, that fills in information appropriate to your own project and database. Make sure to change the username and add your own AWS keys.

*	**Set up the database**
	
	You can choose between using South (for migrations) or Django's built-in syncdb.  
	
	syncdb:
	```bash
	python manage.py syncdb
	```
	
	You may be asked to create a superuser account at some point.  Go ahead and do so.
	
	South:
	```bash
	python manage.py schemamigration retainer --initial
	python manage.py migrate retainer
	```

*	**Test running the server**
	
	To run in development mode, run the following command:
	```bash
	python manage.py runserver 0.0.0.0:someport
	```
	
	Go to localhost:someport/admin and login with the superuser account you just made.  This is the standard Django administration interface.
	
*	**Create a ProtoHIT**
	
	ProtoHITs are the primary relational mapping between categories of work that you want to post HITs for, and the rest of the retainer model.  A simple application will probably have just one ProtoHIT which directs turkers to the appropriate HIT page.  More complicated applications might have different ProtoHITs for different stages of the application, and the same retainer server might have a number of ProtoHITs altogether while it hosts different applications that use the retainer API.
	
	ProtoHITs can either be created via the admin interface or via the `retainer/puttask` POST API.  Before you attempt to use this retainer code for anything, you should have at least one ProtoHIT.
	
	Most ProtoHIT fields correspond closely to the normal MTurk API parameters.  Notable differences include:
	
	*	_Worker Locale_: Instead of a complicated expression, just leave this field empty to avoid restricting workers by locale, or put in a single appropriate country/locale code, like 'US', to restrict to a particular locale.
	*	_Approval Rating_: An integer percent, 0 to 100.  0 is special, and indicates that workers should not be restricted by approval rating.  100% would require perfect workers.

*	**(Optionally) Create an API Key**
	
	If you'd like, create an API in the admin interface.  This adds an `apiKey` parameter to all API methods that will guard access to those pieces of functionality.
	
*	**Create a cron job to run cron.py**
	
	cron.py should run every minute.  It periodically posts HITs for active reservations.  A typical crontab entry for this file looks like this: 
	
	`* * * * * /path/to/cron.py >> /path/to/retainer.log 2>&1`
	
*	**Integrate retainer.js into your landing page**
	
	Your landing page is where turkers will be waiting; this can be either the same page as your HIT (but with some content replaced temporarily) or a whole other page that turkers will see until there is work ready for them.
	
	Make sure that retainer.js points at the correct URLs.  These will be specific to your installation.  You should override (aka reassign) `Retainer.hasWork` to do something related to the task you want your workers to do.  `hasWork` is passed an object with a `taskID` property, which will be the same as the `foreignID` of any reservation (WorkReservation) your system makes.
	
*	**Have your application make WorkReservations**
	
	Using the `retainer/reservation/make`, ...`invoke`, and ...`done` APIs, coordinate the lifecycle of your tasks 
	with whatever application(s) of yours that are using the retainer server.
	
*	**Monitor work progress**

	There is an HTML landing page for monitoring the status of current jobs on retainer.  It's a static set of files in `static/status`. 
	
API
---

```
gettask/assignment/<assignment_id>
retainer/gettask/assignment/<assignment_id>
```

Called by retainer.js.

---

```
ping/worker/<worker_id>/assignment/<assignment_id>/hit/<hit_id>/event/<ping_type>
retainer/ping/worker/<worker_id>/assignment/<assignment_id>/hit/<hit_id>/event/<ping_type>
```

Called by retainer.js.

---

```
puttask
retainer/puttask
```

Used to create ProtoHITs.

---

```
putwork
retainer/putwork
```

_Deprecated_.  Creates WorkRequests.

---

```
putwork/done
retainer/putwork/done
```

_Deprecated_.  Cancels a WorkRequest.

---

```
reservation/make
retainer/reservation/make
```

Creates a WorkReservation.  Indicates that work is incoming, though not necessarily available yet.  Calling 
this method will pre-emptively start posting HITs, though workers will not be directed to the actual task yet.

---

```
reservation/cancel
retainer/reservation/cancel
```

Cancels a reservation.  May be useful for when the end-user makes a mistake or an app crashes.

---

```
reservation/invoke
retainer/reservation/invoke
```

Indicates that a reservation is now being called upon to supply workers to an incoming task.  

---

```
reservation/finish
retainer/reservation/finish
```

Marks a reservation as complete, so no more workers are sent to it.

---
```
reservation/list
retainer/reservation/list
```

Generates JSON to list current reservations and ProtoHITs.

---
```
reservation/finish/all
retainer/reservation/finish/all
```

Convenience API to mark all 
