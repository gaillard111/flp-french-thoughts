<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Type\TopicType;
use Doctrine\ORM\OptimisticLockException;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Topic;

/**
 * @Route("/profile")
 */
class TopicController extends Controller
{
    /**
     * @Route("/topics", name="profile_topics_list")
     * @Route("/student/{user_id}/topics", name="student_topics")
     * @ParamConverter("student", options={"mapping"={"user_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request, User $student = null)
    {
        $user = $this->getUser();

        if (!is_null($student)) {
            $this->denyAccessUnlessGranted($student, $this->getUser());
            $user = $student;
        }

        $em = $this->get('doctrine.orm.entity_manager');

        $role = User::ROLE_USER;

        if ($this->isGranted(User::ROLE_STUDENT)) {
            $role = User::ROLE_STUDENT;
        }

        $topics = $em->getRepository(Topic::class)->searchTopics($role, null, $user);

//        dump($topics); die;

//        $paginator  = $this->get('knp_paginator');
//        $pagination = $paginator->paginate(
//            $topics,
//            $request->query->getInt('page', 1),
//            100
//        );
        return $this->render('ThoughtBundle:Profile/Topics:list.html.twig', [
            'topics' => $topics,
            'student' => $student
        ]);
    }

    /**
     * @Route("/topics/{topicId}", name="topic_page", requirements={"topicId"="\d+"})
     */
    public function indexAction(Request $request)
    {
        $topicId = $request->get('topicId');
        $em      = $this->getDoctrine()->getManager();
        $topic   = $em->getRepository(Topic::class)->find($topicId);

        return $this->render('@Thought/Profile/Topics/topicPage.html.twig', [
            'topic' => $topic,
        ]);
    }

    /**
     * @Route("/topic/create", name="sonata_user_topic_create")
     *
     * @param Request $request
     *
     * @return Response
     *
     * @throws OptimisticLockException
     */
    public function createAction(Request $request)
    {
        $em    = $this->get('doctrine.orm.entity_manager');
        $topic = new Topic();
        $topic->setUser($this->getUser());

        $form = $this->createForm(new TopicType(), $topic);
        $form->handleRequest($request);

        if (($form->isSubmitted()) && ($form->isValid())) {
            $topic = $form->getData();
            $em->persist($topic);
            $em->flush();
            return $this->redirectToRoute('profile_topics_list');
        }

        return $this->render('@Thought/Profile/Topics/create.html.twig', [
            'form' => $form->createView(),
        ]);
    }

    /**
     * @Route("/topic/{topicId}/edit", name="sonata_user_topic_edit", requirements={"topicId"="\d+"})
     * @param Request $request
     * @param $topicId
     * @return RedirectResponse|Response
     * @throws OptimisticLockException
     */
    public function editAction(Request $request, $topicId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Topic $topic */
        $topic = $em->getRepository(Topic::class)->find($topicId);
        $student = null;
        $user  = $this->getUser();
        $ownerTopic = $topic->getUser();

        if ($this->isGranted('ROLE_TEACHER') and ($this->getUser() !== $ownerTopic)) {
            $this->denyAccessUnlessGranted($ownerTopic, $this->getUser());
            $student = $ownerTopic;
        } elseif ($ownerTopic !== $this->getUser()) {
            $this->addFlash('danger', $this->get('translator')->trans('thought.topic.access_denied'));
            return $this->redirectToRoute('profile_topics_list');
        }

        $form = $this->createForm(new TopicType(), $topic);
        $form->handleRequest($request);
        if (($form->isSubmitted()) && ($form->isValid())) {
            $topic = $form->getData();
            $em->persist($topic);
            $em->flush();
            if (!is_null($student)) {
                return $this->redirectToRoute('student_topics', ['user_id' => $student->getId()]);
            } else {
                return $this->redirectToRoute('profile_topics_list');
            }
        }
        return $this->render('@Thought/Profile/Topics/create.html.twig', [
            'form' => $form->createView(),
            'student' => $student
        ]);
    }

    /**
     * @Route("/topic/{topicId}/delete", name="sonata_user_topic_remove", requirements={"topicId"="\d+"})
     */
    public function removeAction($topicId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Topic $topic */
        $topic = $em->getRepository(Topic::class)->find($topicId);
        $em->remove($topic);
        $em->flush();

        return $this->redirectToRoute('profile_topics_list');
    }
}
