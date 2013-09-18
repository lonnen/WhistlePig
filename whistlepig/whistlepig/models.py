from django.db import models
import re

class StatusUpdate(models.Model):
    summary = models.CharField(max_length=255, blank=False)
    posted_by = models.CharField(max_length=255, blank=False)
    duration_minutes = models.IntegerField(null = True, blank=True)
    admin_assigned = models.CharField(max_length=255, blank=False)
    bugzilla_id = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=False, blank=False)
    posted_on = models.DateTimeField(auto_now_add=True)
    severity = models.ForeignKey('Severity')
    status = models.ForeignKey('Status')
    timezone = models.ForeignKey('TimeZone')
    site = models.ForeignKey('Site', null=True)
    from_bugzilla = models.BooleanField()

    search_fields = (
            'summary',
            'description',
            'bugzilla_id',
            'severity__name',
            'posted_by',
            'admin_assigned',
            'serviceoutage__service__name',
    )

    def __unicode__(self):
        return self.summary

    @property
    def event_start_date(self):
        return self.start_time.strftime("%Y-%m-%d")
    
    @property
    def event_start_time(self):
        return self.start_time.strftime("%H:%M")

    @property
    def services(self):
        return ", ".join([s.service.name for s in self.serviceoutage_set.all()])

    @models.permalink
    def get_absolute_url(self):
        return ('article-detail', [self.id])

    def expand_minutes(self):
        input_minutes = self.duration_minutes
        hours = input_minutes / 60
        minutes = input_minutes % 60
        if hours == 1:
            hour_string = 'hour'
        else:
            hour_string = 'hours'

        if minutes == 1:
            minute_string = 'minute'
        else:
            minute_string = 'minutes'

        if hours > 0 and minutes == 0:
            return "%s %s" % (
                    hours,
                    hour_string
                    )

        elif hours == 0 and minutes > 0:
            return "%s %s" % (
                    minutes,
                    minute_string
                    )
        else:                                                                                                             
            return "%s %s %s %s" % (
                    hours,
                    hour_string,
                    minutes,
                    minute_string
                    )

class Severity(models.Model):
    name = models.CharField(max_length=255, blank=False)
    css_class = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

class Status(models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.name
class ServiceOutage(models.Model):
    status_update = models.ForeignKey('StatusUpdate')
    service = models.ForeignKey('Service')

    def __unicode__(self):
        return "%s - %s" % (self.status_update, self.service)

class Service(models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

class SourceEmailAddress(models.Model):
    name = models.CharField(max_length=255, blank=False)
    short_description = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

class TimeZone(models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

class Site(models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

class StatusUpdateComment(models.Model):
    author = models.CharField(max_length=255, blank=False)
    comment = models.TextField(blank=False)
    created_on = models.DateTimeField(auto_now_add=True)
    statusupdate = models.ForeignKey('StatusUpdate')

    def __unicode__(self):
        return "%s - %s" % (self.author, self.created_on)

class DestinationEmailAddress(models.Model):
    name = models.CharField(max_length=255, blank=False)

    def __unicode__(self):
        return self.name

class OutageNotificationTemplate(models.Model):
    interpolated_variable_hash = {}
    name = models.CharField(max_length=255, blank=False)
    outage_notification_template = models.TextField(blank=False)

    def extract_variable_to_interpolate(self, input_line):
        var_re = re.compile('<<([^>><<]*)>>')
        result = var_re.findall(input_line)
        if not result:
            return None
        else:
            rethash = {}
            for r in result:
                rethash['<<%s>>' % r] = r
                self.interpolated_variable_hash['<<%s>>' % r] = r
            return rethash




    def interpolate_template(self, status_update = None, template = None):
        self.status_update = status_update
        if not template:
            template = self.outage_notification_template
        for line in template.split():
            self.extract_variable_to_interpolate(line)
        for k in self.interpolated_variable_hash.iterkeys():
            try:
                template = template.replace(k, str(getattr(status_update, self.interpolated_variable_hash[k])))
                #print "%s found" % self.interpolated_variable_hash[k]
            except (AttributeError):
                #print "%s not found" % self.interpolated_variable_hash[k]
                pass
        return template
        #template = template.replace('<<issue_status_description>>', status_update.summary)
        #template = template.replace('<<issue_status>>', status_update.status.name)
        #template = template.replace('<<bug_ids>>', status_update.bugzilla_id)
        #template = template.replace('<<issue_date>>', status_update.start_time.strftime("%Y-%m-%d"))
        #template = template.replace('<<issue_start_time>>', status_update.start_time.strftime("%H:%M UTC"))
        #template = template.replace('<<issue_duration>>', str(status_update.duration_minutes))
        #template = template.replace('<<services>>', ', '.join([s.service.name for s in status_update.serviceoutage_set.all()]))
        #template = template.replace('<<summary>>', status_update.description)
        #if status_update.site:
        #    template = template.replace('<<issue_site>>', status_update.site.name)
        #return template

    def __init__(self, *args, **kwargs):
        self.interpolated_variable_hash = {}
        super(OutageNotificationTemplate, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return self.name
