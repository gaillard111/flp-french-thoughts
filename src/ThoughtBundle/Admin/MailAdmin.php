<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 03.08.18
 * Time: 12:50
 */

namespace ThoughtBundle\Admin;

use Sonata\AdminBundle\Admin\Admin;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Form\FormMapper;
use ThoughtBundle\Entity\GeneralMail;

class MailAdmin extends Admin
{
    private $rootPath;

    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('subject')
            ->add('body', 'textarea', [
                'label' => 'Message',
                'attr'  => [
                    'class' => 'js-ckeditor',
                ],
            ]);
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('id')
//            ->add('mailTo')
            ->add('subject')
            ->add('body', 'html', [
                'strip' => true
            ])
            ->add('isSended');
    }

    /**
     * @param DatagridMapper $datagridMapper
     */
    protected function configureDatagridFilters(DatagridMapper $datagridMapper)
    {
        foreach ($this->getFilterFields() as $filterField) {
            $datagridMapper->add($filterField);
        }
    }

    /**
     * @return array
     */
    public function getFilterFields()
    {
        return [
            //            'mailTo',
            'subject',
            'body',
            'isSended',
        ];
    }

    public function setMyRootPath($rootPath)
    {
        $this->rootPath = $rootPath;
    }

    public function postPersist($object)
    {
        $this->sendEmailForAllUsers($object);
    }

    public function postUpdate($object)
    {
        $this->sendEmailForAllUsers($object);
    }

    private function sendEmailForAllUsers($object)
    {
        $root = $this->rootPath;
        /** @var GeneralMail $object */
        $mailId  = $object->getId();
        $command = 'nohup php "' . $root . '/console" throught:mail_command ' . $mailId . ' >> ' . $root . '/logs/mail_command_out.log 2>&1 &';

//        dump($command); die;

        exec($command);
    }
}