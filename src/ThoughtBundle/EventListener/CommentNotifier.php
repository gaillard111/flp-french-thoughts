<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 12.08.19
 * Time: 15:22
 */

namespace ThoughtBundle\EventListener;


use Doctrine\Common\Persistence\Event\LifecycleEventArgs;
use Symfony\Component\Stopwatch\Stopwatch;
use ThoughtBundle\Entity\Comment;
use ThoughtBundle\Entity\Like;
use ThoughtBundle\Service\Mail;

class CommentNotifier
{
    /**
     * @var Mail
     */
    private $mailService;

    /**
     * @var Stopwatch
     */
    private $stopwatch;

    public function __construct(Mail $mailService, Stopwatch $stopwatch)
    {
        $this->mailService = $mailService;
        $this->stopwatch = $stopwatch;
    }

    public function postPersist(LifecycleEventArgs $args)
    {
        /** @var Comment|mixed $comment */
        $comment = $args->getObject();
        $thought = $comment->getThought();
        $thoughtOwner = $thought->getOwner();
        /** @var Like[]|mixed $likes */
        $likes = $thought->getLikes();
        $comments = $thought->getComments();

//        $this->stopwatch->start('mailing');

        foreach ($comments as $key => $comment) {

            $comments[$key] = $comment->getEmail();
        }
        $emails = array_unique($comments->toArray());

        foreach ($emails as $email) {
//            dump(1, $email, $comment->getEmail());
            if ($email != $comment->getEmail()) {
                $this->mailService->sendMail('L\'extrait du jour', $email, 'User ' . $comment->getFullName() . ' also commented this thought');
            }

        }


        foreach ($likes as $like) {
//            dump(2, $like->getUser()->getEmail(), $comment->getEmail());
            if ($like->getUser()->getEmail() != $comment->getEmail()) {
                $this->mailService->sendMail('L\'extrait du jour', $like->getUser()->getEmail(), 'Тхоут, который вы лайкнули комментнул ' . $comment->getFullName());
            }


        }

//        dump(3, $thoughtOwner->getEmail(), $comment->getEmail());

        if ($thoughtOwner->getEmail() != $comment->getEmail()) {
            $this->mailService->sendMail('L\'extrait du jour', $thoughtOwner->getEmail(), 'К вашему тхоуту добавили коммент');
        }
//        die;

//        $this->stopwatch->stop('mailing');
    }
}