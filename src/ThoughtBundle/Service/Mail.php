<?php

namespace ThoughtBundle\Service;

use Symfony\Component\DependencyInjection\Container;
use ThoughtBundle\Entity\Comment;

/**
 * Class Mail
 * @package ThoughtBundle\Service
 */
class Mail
{
    /**
     * @var Container
     */
    private $container;

    /**
     * @var \Symfony\Component\Translation\DataCollectorTranslator
     */
    private $translator;

    /**
     * Mail constructor.
     * @param Container $container
     */
    public function __construct(Container $container)
    {
        $this->container = $container;

        $this->translator = $container->get('translator');
    }

    /**
     * Send email - Add new comment
     *
     * @param Comment $comment
     */
    public function mailAddNewComment(Comment $comment)
    {
        $subject = 'French thought: add new comment';

        $link = $this->container->get('router')->generate('thought_thoughtpage_index', array('thoughtId' => $comment->getThought()->getId()), 0);

        $body = 'User: ' . $comment->getFullName() . ' in ' . $comment->getCreatedAt()->format('Y-m-d H:i') .
            ' leave comment: ' . $comment->getText() . '<br>' .
            'To view the review click on the ' . '<a href="' . $link . '">link</a>'
        ;

        $emailUsers = $this->container->getParameter('admin_email');

        $this->sendMail($subject, $emailUsers, $body);
    }

    /**
     * @param string $subject
     * @param array $emailUsers
     * @param string $body
     */
    private function sendMail($subject, $emailUsers, $body, $cc = null)
    {
        $message = \Swift_Message::newInstance()
            ->setSubject($subject)
            ->setFrom($this->container->getParameter('mailer_user'))
            ->setTo($emailUsers)
            ->setBody($body, 'text/html')
        ;

        if ($cc) {
            $message->setCc($cc);
        }

        $this->container->get('mailer')->send($message);
    }
}
